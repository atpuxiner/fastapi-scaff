import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.initializer.context import request_id_ctx_var


class HeadersMiddleware(BaseHTTPMiddleware):
    """头处理中间件"""
    _HEADERS = {
        # 可添加相关头
    }

    async def dispatch(self, request: Request, call_next):
        request_id = self._get_or_create_request_id(request)
        request.state.request_id = request_id
        ctx_token = request_id_ctx_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            for key, value in self._HEADERS.items():
                if key not in response.headers:
                    response.headers[key] = value
            return response
        finally:
            request_id_ctx_var.reset(ctx_token)

    @staticmethod
    def _get_or_create_request_id(request: Request) -> str:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req-{uuid.uuid4()}"
        return request_id
