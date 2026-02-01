"""
中间件
"""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app.api.exceptions import CustomException
from app.middleware.cors import CorsMiddleware
from app.middleware.exceptions import ExceptionsHandler
from app.middleware.http import HttpMiddleware


def register_middlewares(app: FastAPI):
    """注册中间件 & 错误处理"""
    app.add_middleware(CorsMiddleware)
    app.add_middleware(HttpMiddleware)
    # #
    app.add_exception_handler(CustomException, ExceptionsHandler.custom_exception_handler)
    app.add_exception_handler(RequestValidationError, ExceptionsHandler.request_validation_handler)
    app.add_exception_handler(HTTPException, ExceptionsHandler.http_exception_handler)
