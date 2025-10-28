from starlette.middleware.cors import CORSMiddleware

from app.initializer import g


class Cors:
    middleware_class = CORSMiddleware
    allow_origins = g.config.app_allow_origins
    allow_credentials = True
    allow_methods = ["*"]
    allow_headers = ["*"]
