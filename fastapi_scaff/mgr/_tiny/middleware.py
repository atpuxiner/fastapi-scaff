"""
中间件
"""

import logging
import uuid

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.exceptions import CustomException
from app.api.responses import Responses
from app.api.status import Status
from app.initializer import g, request_id_var

__all__ = [
    "register_middlewares",
]

logger = logging.getLogger(__name__)


def register_middlewares(app: FastAPI):
    """注册中间件"""
    app.add_middleware(CorsMiddleware)
    app.add_middleware(HttpMiddleware)
    # #
    app.add_exception_handler(CustomException, ExceptionsHandler.custom_exception_handler)
    app.add_exception_handler(RequestValidationError, ExceptionsHandler.request_validation_handler)
    app.add_exception_handler(HTTPException, ExceptionsHandler.http_exception_handler)


class CorsMiddleware(CORSMiddleware):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            allow_credentials=g.config.APP_ALLOW_CREDENTIALS,
            allow_origins=g.config.APP_ALLOW_ORIGINS,
            allow_methods=g.config.APP_ALLOW_METHODS,
            allow_headers=g.config.APP_ALLOW_HEADERS,
            **kwargs,
        )


class HttpMiddleware(BaseHTTPMiddleware):
    _HEADERS = {
        # 可添加相关头
    }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = self._get_or_create_request_id(request)
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            for key, value in self._HEADERS.items():
                if key not in response.headers:
                    response.headers[key] = value
            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)
        finally:
            request_id_var.reset(token)

    @staticmethod
    def _get_or_create_request_id(request: Request, prefix: str = "req-") -> str:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"{prefix}{uuid.uuid4().hex}"
        return request_id

    @staticmethod
    async def handle_exception(
        request: Request,
        exc: Exception,
        log_traceback: bool = True,
        log_request: bool = False,
    ) -> JSONResponse:
        lmsg = (
            f'- "{request.method} {request.url.path}" {Status.INTERNAL_SERVER_ERROR.code} {type(exc).__name__}: {exc}'
        )
        if log_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
        if log_request:
            logger.warning(f"Query params: {request.query_params or '<Empty>'}")
            logger.warning(f"Body: {await request.body() or b'<Empty>'!r}")
        return Responses.failure(
            error=exc,
            status=Status.INTERNAL_SERVER_ERROR,
        )


class ExceptionsHandler:
    @staticmethod
    async def custom_exception_handler(
        request: Request,
        exc: CustomException,
        log_traceback: bool = True,
        log_request: bool = False,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.code} {exc.msg}'
        if log_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
        if log_request:
            logger.warning(f"Query params: {request.query_params or '<Empty>'}")
            logger.warning(f"Body: {await request.body() or b'<Empty>'!r}")
        return Responses.failure(
            msg=exc.msg,
            code=exc.code,
            error=exc,
            data=exc.data,
        )

    @staticmethod
    async def request_validation_handler(
        request: Request,
        exc: RequestValidationError,
        display_all: bool = False,
        log_traceback: bool = True,
        log_request: bool = False,
    ) -> JSONResponse:
        if display_all:
            msg = " & ".join(
                [
                    f"{error['loc'][-1]} ({error['type']}) {error['msg'].replace('Value error, ', '').lower()}"
                    for error in exc.errors()
                ]
            )
        else:
            error = exc.errors()[0]
            msg = f"{error['loc'][-1]} ({error['type']}) {error['msg'].replace('Value error, ', '').lower()}"
        lmsg = f'- "{request.method} {request.url.path}" {Status.PARAMS_ERROR.code} {msg}'
        if log_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
        if log_request:
            logger.warning(f"Query params: {request.query_params or '<Empty>'}")
            logger.warning(f"Body: {await request.body() or b'<Empty>'!r}")
        return Responses.failure(
            msg=msg,
            error=exc,
            status=Status.PARAMS_ERROR,
        )

    @staticmethod
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
        log_traceback: bool = True,
        log_request: bool = False,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.status_code} {exc.detail}'
        if log_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
        if log_request:
            logger.warning(f"Query params: {request.query_params or '<Empty>'}")
            logger.warning(f"Body: {await request.body() or b'<Empty>'!r}")
        return Responses.failure(
            msg=exc.detail,
            code=exc.status_code,
            error=exc,
        )
