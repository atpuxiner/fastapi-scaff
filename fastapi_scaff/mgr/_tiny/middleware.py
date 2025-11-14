"""
中间件
"""
import uuid

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.exceptions import CustomException
from app.api.responses import Responses
from app.api.status import Status
from app.initializer import g, request_id_var

__all__ = [
    "register_middlewares",
]


def register_middlewares(app: FastAPI):
    """注册中间件"""
    app.add_middleware(
        middleware_class=CORSMiddleware,  # type: ignore
        allow_credentials=True,
        allow_origins=g.config.app_allow_origins,
        allow_methods=g.config.app_allow_methods,
        allow_headers=g.config.app_allow_headers,
    )
    app.add_middleware(HeadersMiddleware)  # type: ignore
    app.add_exception_handler(CustomException, ExceptionsHandler.custom_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, ExceptionsHandler.request_validation_handler)  # type: ignore
    app.add_exception_handler(HTTPException, ExceptionsHandler.http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, ExceptionsHandler.exception_handler)


class HeadersMiddleware(BaseHTTPMiddleware):
    """头处理中间件"""
    _HEADERS = {
        # 可添加相关头
    }

    async def dispatch(self, request: Request, call_next):
        request_id = self._get_or_create_request_id(request)
        request.state.request_id = request_id
        ctx_token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            for key, value in self._HEADERS.items():
                if key not in response.headers:
                    response.headers[key] = value
            return response
        finally:
            request_id_var.reset(ctx_token)

    @staticmethod
    def _get_or_create_request_id(request: Request, prefix: str = "req-") -> str:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"{prefix}{uuid.uuid4()}"
        return request_id


class ExceptionsHandler:

    @staticmethod
    async def custom_exception_handler(
            request: Request,
            exc: CustomException,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.code} {exc.msg}'
        g.logger.exception(lmsg)
        return Responses.failure(
            msg=exc.msg,
            code=exc.code,
            data=exc.data,
        )

    @staticmethod
    async def request_validation_handler(
            request: Request,
            exc: RequestValidationError,
            is_display_all: bool = False,
    ) -> JSONResponse:
        if is_display_all:
            msg = " & ".join([
                f"{error['loc'][-1]} ({error['type']}) {error['msg'].replace('Value error, ', '').lower()}"
                for error in exc.errors()
            ])
        else:
            error = exc.errors()[0]
            msg = f"{error['loc'][-1]} ({error['type']}) {error['msg'].replace('Value error, ', '').lower()}"
        lmsg = f'- "{request.method} {request.url.path}" {Status.PARAMS_ERROR.code} {msg}'
        g.logger.error(lmsg)
        return Responses.failure(
            msg=msg,
            status=Status.PARAMS_ERROR,
        )

    @staticmethod
    async def http_exception_handler(
            request: Request,
            exc: HTTPException,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.status_code} {exc.detail}'
        g.logger.exception(lmsg)
        return Responses.failure(
            msg=exc.detail,
            code=exc.status_code,
        )

    @staticmethod
    async def exception_handler(
            request: Request,
            exc: Exception,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" 500 {type(exc).__name__}: {exc}'
        g.logger.exception(lmsg)
        return Responses.failure(
            msg="Internal system error, please try again later.",
            code=500,
        )
