from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.core import config, logger
from app.middleware import add_middleware_and_exceptions

openapi_url, docs_url, redoc_url = "/openapi.json", "/docs", "/redoc"
if config.APP_DISABLE_DOCS is True:
    openapi_url, docs_url, redoc_url = None, None, None


@asynccontextmanager
async def lifespan(xapp: FastAPI):
    logger.info(f"Application env '{config.APP_ENV}'")
    logger.info(f"Application yaml '{config.YAML_PATH}'")
    logger.info(f"Application title '{config.APP_TITLE}'")
    logger.info(f"Application version '{config.APP_VERSION}'")
    # #
    logger.info("Application server running")
    yield
    logger.info("Application server shutdown")


app = FastAPI(
    title=config.APP_TITLE,
    summary=config.APP_SUMMARY,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
    debug=config.APP_DEBUG,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
)
# #
add_middleware_and_exceptions(app)
app.include_router(router)
