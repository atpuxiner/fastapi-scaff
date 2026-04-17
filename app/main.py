"""
@author axiner
@version v1.0.0
@created 2024/07/29 22:22
@abstract 主入口
@description
@history
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app import (
    api,
    middleware,
)
from app.initializer import g

g.setup()
# #
openapi_url = "/openapi.json"
docs_url = "/docs"
redoc_url = "/redoc"
if g.config.APP_DISABLE_DOCS is True:
    openapi_url, docs_url, redoc_url = None, None, None


@asynccontextmanager
async def lifespan(xapp: FastAPI):
    g.logger.info(f"Application env '{g.config.APP_ENV}'")
    g.logger.info(f"Application yaml '{g.config.YAML_PATH.name}'")
    g.logger.info(f"Application title '{g.config.APP_TITLE}'")
    g.logger.info(f"Application version '{g.config.APP_VERSION}'")
    # #
    g.logger.info("Application server running")
    yield
    g.logger.info("Application server shutdown")


app = FastAPI(
    title=g.config.APP_TITLE,
    summary=g.config.APP_SUMMARY,
    description=g.config.APP_DESCRIPTION,
    version=g.config.APP_VERSION,
    debug=g.config.APP_DEBUG,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)
# #
middleware.register_middlewares(app)
api.register_routers(app)
