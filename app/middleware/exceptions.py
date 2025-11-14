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
        g.logger.exception(lmsg)
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
