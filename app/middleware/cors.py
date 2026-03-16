from starlette.middleware.cors import CORSMiddleware

from app.initializer import g


class CorsMiddleware(CORSMiddleware):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            allow_credentials=g.config.APP_ALLOW_CREDENTIALS,
            allow_origins=g.config.APP_ALLOW_ORIGINS,
            allow_methods=g.config.APP_ALLOW_METHODS,
            allow_headers=g.config.APP_ALLOW_HEADERS,
            **kwargs,
        )
