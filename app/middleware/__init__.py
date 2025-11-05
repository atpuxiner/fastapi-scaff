"""
中间件
"""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app.api.exceptions import CustomException
from app.middleware.cors import Cors
from app.middleware.exceptions import ExceptionsHandler
from app.middleware.headers import HeadersMiddleware


def register_middlewares(app: FastAPI):
    """注册中间件"""
    app.add_middleware(
        middleware_class=Cors.middleware_class,
        allow_credentials=Cors.allow_credentials,
        allow_origins=Cors.allow_origins,
        allow_methods=Cors.allow_methods,
        allow_headers=Cors.allow_headers,
    )
    app.add_middleware(HeadersMiddleware)  # type: ignore
    app.add_exception_handler(CustomException, ExceptionsHandler.custom_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, ExceptionsHandler.request_validation_handler)  # type: ignore
    app.add_exception_handler(HTTPException, ExceptionsHandler.http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, ExceptionsHandler.exception_handler)
