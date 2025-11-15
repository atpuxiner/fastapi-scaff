from fastapi.exceptions import RequestValidationError
from loguru import logger
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.exceptions import CustomException
from app.api.responses import Responses
from app.api.status import Status


class ExceptionsHandler:

    @staticmethod
    async def custom_exception_handler(
            request: Request,
            exc: CustomException,
            is_traceback: bool = True,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.code} {exc.msg}'
        if is_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
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
            is_traceback: bool = True,
    ) -> JSONResponse:
        if display_all:
            msg = " & ".join([
                f"{error['loc'][-1]} ({error['type']}) {error['msg'].replace('Value error, ', '').lower()}"
                for error in exc.errors()
            ])
        else:
            error = exc.errors()[0]
            msg = f"{error['loc'][-1]} ({error['type']}) {error['msg'].replace('Value error, ', '').lower()}"
        lmsg = f'- "{request.method} {request.url.path}" {Status.PARAMS_ERROR.code} {msg}'
        if is_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
        return Responses.failure(
            msg=msg,
            error=exc,
            status=Status.PARAMS_ERROR,
        )

    @staticmethod
    async def http_exception_handler(
            request: Request,
            exc: HTTPException,
            is_traceback: bool = True,
    ) -> JSONResponse:
        lmsg = f'- "{request.method} {request.url.path}" {exc.status_code} {exc.detail}'
        if is_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
        return Responses.failure(
            msg=exc.detail,
            code=exc.status_code,
            error=exc,
        )
