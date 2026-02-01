import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from toollib.logu import init_logger

from app.api import router
from app.core import config, request_id_var

_EXPOSE_ERROR = True

enable_console, enable_file = True, True
if config.app_env == "prod":
    enable_console, enable_file = False, True  # 按需调整
logger = init_logger(
    __name__,
    level="DEBUG" if config.app_debug else "INFO",
    request_id_var=request_id_var,
    serialize=config.app_log_serialize,
    enable_console=enable_console,
    enable_file=enable_file,
    outdir=config.app_log_outdir,
)
# logger.add 可添加其他 handler
# #
openapi_url = "/openapi.json"
docs_url = "/docs"
redoc_url = "/redoc"
if config.app_disable_docs is True:
    openapi_url, docs_url, redoc_url = None, None, None


@asynccontextmanager
async def lifespan(xapp: FastAPI):
    logger.info(f"Application env '{config.app_env}'")
    logger.info(f"Application yaml '{config.yaml_path.name}'")
    logger.info(f"Application title '{config.app_title}'")
    logger.info(f"Application version '{config.app_version}'")
    # #
    logger.info("Application server running")
    yield
    logger.info("Application server shutdown")


class CorsMiddleware(CORSMiddleware):
    def __init__(self, xapp, **kwargs):
        super().__init__(
            xapp,
            allow_credentials=config.app_allow_credentials,
            allow_origins=config.app_allow_origins,
            allow_methods=config.app_allow_methods,
            allow_headers=config.app_allow_headers,
            **kwargs
        )


class HttpMiddleware(BaseHTTPMiddleware):
    _HEADERS = {
        # 可添加相关头
    }

    async def dispatch(
            self, request: Request,
            call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = self._get_or_create_request_id(request)
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
    def _get_or_create_request_id(request: Request, prefix: str = "req-") -> str:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"{prefix}{uuid.uuid4().hex}"
        return request_id

    @staticmethod
    async def handle_exception(
            request: Request,
            exc: Exception,
            is_traceback: bool = True,
    ) -> JSONResponse:
        msg = "内部服务器错误"
        code = 500
        lmsg = f'- "{request.method} {request.url.path}" {code} {type(exc).__name__}: {exc}'
        if is_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
        content = {
            "msg": msg,
            "code": code,
            "request_id": request.state.request_id,
        }
        if _EXPOSE_ERROR:
            content["error"] = str(exc)
        return JSONResponse(
            content=content,
        )


class ExceptionsHandler:

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
        code = 400
        lmsg = f'- "{request.method} {request.url.path}" {code} {msg}'
        if is_traceback:
            logger.exception(lmsg)
        else:
            logger.error(lmsg)
        content = {
            "msg": msg,
            "code": code,
            "request_id": request.state.request_id,
        }
        if _EXPOSE_ERROR:
            content["error"] = str(exc)
        return JSONResponse(
            content=content,
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
        content = {
            "msg": exc.detail,
            "code": exc.status_code,
            "request_id": request.state.request_id,
        }
        if _EXPOSE_ERROR:
            content["error"] = str(exc)
        return JSONResponse(
            content=content,
        )


app = FastAPI(
    title=config.app_title,
    summary=config.app_summary,
    description=config.app_description,
    version=config.app_version,
    debug=config.app_debug,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)
# #
app.add_middleware(CorsMiddleware)
app.add_middleware(HttpMiddleware)
app.add_exception_handler(RequestValidationError, ExceptionsHandler.request_validation_handler)
app.add_exception_handler(HTTPException, ExceptionsHandler.http_exception_handler)
app.include_router(router)
