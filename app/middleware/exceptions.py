import traceback

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.exceptions import CustomException
from app.api.responses import Responses
from app.api.status import Status
from app.initializer import g


class ExceptionsHandler:

    @staticmethod
    async def custom_exception_handler(
            request: Request,
            exc: CustomException,
            is_traceback: bool = False,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.code} {exc.msg}'
        if is_traceback:
            lmsg = traceback.format_exc()
        g.logger.error(lmsg)
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
            is_traceback: bool = False,
    ) -> JSONResponse:
        if is_display_all:
            msg = ", ".join([f"'{item['loc'][1] if len(item['loc']) > 1 else item['loc'][0]}' {item['msg'].lower()}" for item in exc.errors()])  # noqa: E501
        else:
            _first_error = exc.errors()[0]
            msg = f"'{_first_error['loc'][1] if len(_first_error['loc']) > 1 else _first_error['loc'][0]}' {_first_error['msg'].lower()}"  # noqa: E501
        lmsg = f'- "{request.method} {request.url.path}" {Status.PARAMS_ERROR.code} {msg}'
        if is_traceback:
            lmsg = traceback.format_exc()
        g.logger.error(lmsg)
        return Responses.failure(
            msg=msg,
            status=Status.PARAMS_ERROR,
            request=request,
        )

    @staticmethod
    async def http_exception_handler(
            request: Request,
            exc: HTTPException,
            is_traceback: bool = False,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.status_code} {exc.detail}'
        if is_traceback:
            lmsg = traceback.format_exc()
        g.logger.error(lmsg)
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
        if is_traceback:
            lmsg = traceback.format_exc()
        g.logger.error(lmsg)
        return Responses.failure(
            msg="Internal system error, please try again later.",
            code=500,
            request=request,
        )
