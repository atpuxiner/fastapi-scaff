import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class HeadersMiddleware(BaseHTTPMiddleware):
    """HTTP 头处理中间件"""
    _HEADERS = {
        # 可添加相关头
    }

    async def dispatch(self, request: Request, call_next):
        # 1. 处理请求ID
        request_id = self._get_or_create_request_id(request)
        request.state.request_id = request_id
        # 2. 处理请求
        response = await call_next(request)
        # 3. 添加响应头
        response.headers["X-Request-ID"] = request_id
        for key, value in self._HEADERS.items():
            if key not in response.headers:
                response.headers[key] = value
        return response

    @staticmethod
    def _get_or_create_request_id(request: Request) -> str:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        return request_id
