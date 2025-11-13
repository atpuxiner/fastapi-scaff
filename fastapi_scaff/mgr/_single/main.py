from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from toollib.log import init_logger

from app.api import router
from app.core import config

config.setup()
logger = init_logger(
    __name__,
    level="DEBUG" if config.app_debug else "INFO",
    serialize=config.app_log_serialize,
    basedir=config.app_log_basedir,
)
# #
openapi_url = "/openapi.json"
docs_url = "/docs"
redoc_url = "/redoc"
if config.app_disable_docs is True:
    openapi_url, docs_url, redoc_url = None, None, None


@asynccontextmanager
async def lifespan(app_: FastAPI):
    logger.info(f"Application env '{config.app_env}'")
    logger.info(f"Application yaml '{config.app_yaml.name}'")
    logger.info(f"Application title '{config.app_title}'")
    logger.info(f"Application version '{config.app_version}'")
    # #
    logger.info("Application server running")
    yield
    logger.info("Application server shutdown")


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
app.include_router(router)
app.add_middleware(
    CORSMiddleware,  # noqa
    allow_credentials=True,
    allow_origins=config.app_allow_origins,
    allow_methods=config.app_allow_methods,
    allow_headers=config.app_allow_headers,
)
