"""
中间件
"""

import ipaddress
import json
import re
import uuid
from functools import cache

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core import g
from app.core.context import client_ip_var, request_id_var
from app.core.exceptions import CustomException
from app.core.responses import Responses
from app.core.status import Status

__all__ = [
    "add_middleware_and_exceptions",
]

_REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_MAX_LENGTH = 64
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_SENSITIVE_FIELDS = (
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "authorization",
    "api_key",
    "apikey",
    "access_key",
    "id_card",
    "idcard",
    "phone",
)
_SENSITIVE_FIELD_PATTERN = "|".join(re.escape(field) for field in _SENSITIVE_FIELDS)
_SENSITIVE_KEY_RE = re.compile(
    rf'"[^"]*(?:{_SENSITIVE_FIELD_PATTERN})[^"]*"\s*:\s*"[^"]*"',
    re.IGNORECASE,
)
_MAX_BODY_LOG_LENGTH = 2048
_MAX_CACHED_BODY_SIZE = 64 * 1024
_BODY_STATE_KEY = "_http_middleware_request_body"
_BODY_TRUNCATED_KEY = "_http_middleware_request_body_truncated"


@cache
def _expose_error() -> bool:
    return bool(getattr(g.config, "APP_DEBUG", False))


def _is_sensitive(key: object) -> bool:
    text = str(key).lower()
    return any(field in text for field in _SENSITIVE_FIELDS)


def _mask_data(data):
    if isinstance(data, dict):
        return {
            key: ("***" if _is_sensitive(key) else _mask_data(value))
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [_mask_data(item) for item in data]
    if isinstance(data, tuple):
        return tuple(_mask_data(item) for item in data)
    return data


async def _read_log_body(request: Request) -> str | None:
    state = request.scope.setdefault("state", {})
    raw = state.get(_BODY_STATE_KEY)
    body = bytes(raw) if raw is not None and not isinstance(raw, bytes) else raw
    body_truncated = bool(state.get(_BODY_TRUNCATED_KEY, False))
    if body is None:
        try:
            body = await request.body()
        except Exception:
            return "<unavailable>"
        state[_BODY_STATE_KEY] = body
    if not body:
        return None
    text = body.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        masked = _SENSITIVE_KEY_RE.sub(
            lambda match: f'{match.group(0).split(":", 1)[0]}: "***"',
            text,
        )
    else:
        masked = json.dumps(_mask_data(parsed), ensure_ascii=False)
    if len(masked) > _MAX_BODY_LOG_LENGTH:
        masked = f"{masked[:_MAX_BODY_LOG_LENGTH]}...<truncated>"
    if body_truncated:
        masked += "...<body truncated>"
    return masked


async def _build_error_context(request: Request, log_request: bool) -> str:
    if not log_request:
        return ""
    query_params = [
        (key, "***" if _is_sensitive(key) else value)
        for key, value in request.query_params.multi_items()
    ]
    body = await _read_log_body(request)
    lines = []
    if query_params:
        lines.append(f"Query params: {query_params!r}")
    if body is not None:
        lines.append(f"Body: {body!r}")
    return "\n" + "\n".join(lines) if lines else ""


async def _log_error(
    request: Request,
    exc: Exception,
    *,
    status_code: int,
    biz_code: int | str | None = None,
    detail: str | None = None,
    log_traceback: bool | None = None,
    log_request: bool = True,
) -> None:
    if log_traceback is None:
        log_traceback = status_code >= 500
    ctx = await _build_error_context(request, log_request)
    code = biz_code if biz_code is not None else status_code
    message = detail if detail is not None else str(exc)
    lmsg = f'- "{request.method} {request.url.path}" {code} {type(exc).__name__}: {ctx}\n{message}'
    if log_traceback:
        g.logger.exception(lmsg)
    elif status_code >= 500:
        g.logger.error(lmsg)
    else:
        g.logger.warning(lmsg)


def _format_validation_error(error: dict) -> str:
    loc = error.get("loc") or ()
    field = loc[-1] if loc else "<unknown>"
    error_type = error.get("type", "")
    message = error.get("msg", "").replace("Value error, ", "")
    if error_type:
        return f"{field} ({error_type}) {message}".lower()
    return f"{field} {message}".lower()


def add_middleware_and_exceptions(app: FastAPI):
    """注册中间件&异常处理"""
    # add_middleware 为头插：最后注册的 CorsMiddleware 在最外层，
    # 保证 HttpMiddleware 返回的异常响应也能带上 CORS 头。
    app.add_middleware(HttpMiddleware)
    app.add_middleware(CorsMiddleware)
    # #
    app.add_exception_handler(CustomException, ExceptionsHandler.custom_exception_handler)
    app.add_exception_handler(RequestValidationError, ExceptionsHandler.request_validation_handler)
    app.add_exception_handler(HTTPException, ExceptionsHandler.http_exception_handler)


class HttpMiddleware:
    """纯 ASGI 中间件：注入请求上下文、统一响应头、兜底异常。"""

    _HEADERS = {
        # 可添加相关头
    }

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        body_buffer = bytearray()
        body_truncated = False
        body_complete = False

        async def receive_with_body_cache() -> Message:
            nonlocal body_truncated, body_complete
            message = await receive()
            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                more_body = message.get("more_body", False)
                if not more_body:
                    body_complete = True
                if chunk:
                    if len(body_buffer) < _MAX_CACHED_BODY_SIZE:
                        remaining = _MAX_CACHED_BODY_SIZE - len(body_buffer)
                        take = min(len(chunk), remaining)
                        body_buffer.extend(chunk[:take])
                        if len(chunk) > take:
                            body_truncated = True
                    else:
                        body_truncated = True
                if more_body and len(body_buffer) >= _MAX_CACHED_BODY_SIZE:
                    body_truncated = True
                # 每收到一段就更新缓存，避免 body 未读完就抛异常时拿不到已到达的数据。
                state[_BODY_STATE_KEY] = body_buffer
                state[_BODY_TRUNCATED_KEY] = body_truncated
            elif message["type"] == "http.disconnect":
                if not body_complete:
                    body_truncated = True
                state[_BODY_STATE_KEY] = body_buffer
                state[_BODY_TRUNCATED_KEY] = body_truncated
            return message

        request_id_token = None
        client_ip_token = None
        try:
            request = Request(scope, receive_with_body_cache)
            request_id = self._get_or_create_request_id(request, key=_REQUEST_ID_HEADER)
            request_id_token = request_id_var.set(request_id)
            client_ip = self._get_client_ip(request)
            client_ip_token = client_ip_var.set(client_ip)
            request.state.request_id = request_id
            request.state.client_ip = client_ip

            response_started = False

            async def send_with_headers(message: Message) -> None:
                nonlocal response_started
                if message["type"] == "http.response.start":
                    response_started = True
                    headers = MutableHeaders(scope=message)
                    headers[_REQUEST_ID_HEADER] = request_id
                    for key, value in self._HEADERS.items():
                        if key not in headers:
                            headers[key] = value
                await send(message)

            try:
                await self.app(scope, receive_with_body_cache, send_with_headers)
            except Exception as exc:
                if response_started:
                    raise
                response = await self.handle_exception(request, exc)
                await response(scope, receive_with_body_cache, send_with_headers)
        finally:
            if request_id_token is not None:
                request_id_var.reset(request_id_token)
            if client_ip_token is not None:
                client_ip_var.reset(client_ip_token)

    @staticmethod
    def _get_or_create_request_id(request: Request, key: str = _REQUEST_ID_HEADER) -> str:
        request_id = request.headers.get(key)
        if request_id:
            request_id = request_id.strip()
            if 0 < len(request_id) <= _REQUEST_ID_MAX_LENGTH and _REQUEST_ID_RE.fullmatch(request_id):
                return request_id
        return str(uuid.uuid4())

    @staticmethod
    def _get_client_ip(request: Request, default: str = "-") -> str:
        candidates = []
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            candidates.extend(part.strip() for part in forwarded_for.split(","))
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            candidates.append(real_ip.strip())
        for candidate in candidates:
            if not candidate:
                continue
            try:
                return str(ipaddress.ip_address(candidate))
            except ValueError:
                continue
        if request.client and request.client.host:
            return request.client.host
        return default

    @staticmethod
    async def handle_exception(
        request: Request,
        exc: Exception,
        log_traceback: bool | None = None,
        log_request: bool = True,
    ) -> JSONResponse:
        await _log_error(
            request,
            exc,
            status_code=Status.INTERNAL_SERVER_ERROR.status_code,
            biz_code=Status.INTERNAL_SERVER_ERROR.code,
            log_traceback=log_traceback,
            log_request=log_request,
        )
        return Responses.failure(
            status=Status.INTERNAL_SERVER_ERROR,
            error=exc if _expose_error() else None,
        )


class CorsMiddleware(CORSMiddleware):
    def __init__(self, app, **kwargs):
        allow_credentials = kwargs.pop("allow_credentials", g.config.APP_ALLOW_CREDENTIALS)
        allow_origins = kwargs.pop("allow_origins", g.config.APP_ALLOW_ORIGINS)
        allow_methods = kwargs.pop("allow_methods", g.config.APP_ALLOW_METHODS)
        allow_headers = kwargs.pop("allow_headers", g.config.APP_ALLOW_HEADERS)
        if allow_credentials and "*" in allow_origins:
            g.logger.warning(
                "CORS: allow_origins contains '*' while allow_credentials=True; "
                "browsers may reject this combination."
            )
        super().__init__(
            app,
            allow_credentials=allow_credentials,
            allow_origins=allow_origins,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            **kwargs,
        )


class ExceptionsHandler:
    @staticmethod
    async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
        status_code = getattr(exc.status, "status_code", 500)
        await _log_error(
            request,
            exc,
            status_code=status_code,
            biz_code=exc.code,
            detail=exc.msg,
        )
        return Responses.failure(
            status=exc.status,
            msg=exc.msg,
            code=exc.code,
            error=exc.error if _expose_error() else None,
            data=exc.data,
        )

    @staticmethod
    async def request_validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = exc.errors()
        if errors:
            selected = errors if _expose_error() else errors[:1]
            msg = " & ".join(_format_validation_error(error) for error in selected)
        else:
            msg = Status.VALIDATION_ERROR.msg
        await _log_error(
            request,
            exc,
            status_code=Status.VALIDATION_ERROR.status_code,
            biz_code=Status.VALIDATION_ERROR.code,
            detail=msg,
        )
        return Responses.failure(
            status=Status.VALIDATION_ERROR,
            msg=msg,
            error=exc if _expose_error() else None,
        )

    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        status = Status.from_status_code(exc.status_code)
        detail = exc.detail
        if isinstance(detail, str):
            msg = detail
        else:
            try:
                msg = json.dumps(detail, ensure_ascii=False)
            except (TypeError, ValueError):
                msg = str(detail)
        await _log_error(
            request,
            exc,
            status_code=exc.status_code,
            biz_code=status.code,
            detail=msg,
        )
        return Responses.failure(
            status=status,
            msg=msg,
            error=exc if _expose_error() else None,
            status_code=exc.status_code,
            headers=exc.headers,
        )
