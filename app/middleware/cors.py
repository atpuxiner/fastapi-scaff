from starlette.middleware.cors import CORSMiddleware

from app.initializer import g


class CorsMiddleware(CORSMiddleware):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            allow_credentials=g.config.app_allow_credentials,
            allow_origins=g.config.app_allow_origins,
            allow_methods=g.config.app_allow_methods,
            allow_headers=g.config.app_allow_headers,
            **kwargs
        )
