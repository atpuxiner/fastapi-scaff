"""
中间件
"""
import traceback
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
            is_traceback: bool = True,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.code} {exc.msg}'
        g.logger.error(lmsg)
        if is_traceback:
            g.logger.error(traceback.format_exc())
        return Responses.failure(
            msg=exc.msg,
            code=exc.code,
            data=exc.data,
            request=request,
        )

    @staticmethod
    async def request_validation_handler(
            request: Request,
            exc: RequestValidationError,
            is_display_all: bool = False,
            is_traceback: bool = True,
    ) -> JSONResponse:
        if is_display_all:
            msg = ", ".join(
                [f"'{item['loc'][1] if len(item['loc']) > 1 else item['loc'][0]}' {item['msg'].lower()}"
                 for item in exc.errors()]
            )
        else:
            _first_error = exc.errors()[0]
            msg = f"'{_first_error['loc'][1] if len(_first_error['loc']) > 1 else _first_error['loc'][0]}' {_first_error['msg'].lower()}"  # noqa: E501
        lmsg = f'- "{request.method} {request.url.path}" {Status.PARAMS_ERROR.code} {msg}'
        g.logger.error(lmsg)
        if is_traceback:
            g.logger.error(traceback.format_exc())
        return Responses.failure(
            msg=msg,
            status=Status.PARAMS_ERROR,
            request=request,
        )

    @staticmethod
    async def http_exception_handler(
            request: Request,
            exc: HTTPException,
            is_traceback: bool = True,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.status_code} {exc.detail}'
        g.logger.error(lmsg)
        if is_traceback:
            g.logger.error(traceback.format_exc())
        return Responses.failure(
            msg=exc.detail,
            code=exc.status_code,
            request=request,
        )

    @staticmethod
    async def exception_handler(
            request: Request,
            exc: Exception,
            is_traceback: bool = True,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" 500 {type(exc).__name__}: {exc}'
        g.logger.error(lmsg)
        if is_traceback:
            g.logger.error(traceback.format_exc())
        return Responses.failure(
            msg="Internal system error, please try again later.",
            code=500,
            request=request,
        )
