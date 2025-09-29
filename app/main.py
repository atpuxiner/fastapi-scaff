"""
@author axiner
@version v1.0.0
@created 2024/07/29 22:22
@abstract main
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
if g.config.app_disable_docs is True:
    openapi_url, docs_url, redoc_url = None, None, None


@asynccontextmanager
async def lifespan(app_: FastAPI):
    g.logger.info(f"Application env '{g.config.app_env}'")
    g.logger.info(f"Application yaml '{g.config.app_yaml}'")
    g.logger.info(f"Application title '{g.config.app_title}'")
    g.logger.info(f"Application version '{g.config.app_version}'")
    # #
    g.logger.info("Application server running")
    yield
    g.logger.info("Application server shutdown")


app = FastAPI(
    title=g.config.app_title,
    summary=g.config.app_summary,
    description=g.config.app_description,
    version=g.config.app_version,
    debug=g.config.app_debug,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)
# #
api.register_routers(app)
middleware.register_middlewares(app)
