import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.responses import Responses
from app.api.status import Status
from app.initializer.context import request_id_var

logger = logging.getLogger(__name__)


class HttpMiddleware(BaseHTTPMiddleware):
    _HEADERS = {
        # 可添加相关头
    }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = await self._get_or_create_request_id(request)
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
    async def _get_or_create_request_id(request: Request, prefix: str = "req-") -> str:
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
