from fastapi import Response

_REFRESH_TOKEN_COOKIE_NAME = "x_refresh_token"
_REFRESH_TOKEN_PATH = "/api"


def set_refresh_token_cookie(
    response: Response,
    refresh_token: str,
    max_age: int,
    cookie_name: str = _REFRESH_TOKEN_COOKIE_NAME,
    path: str = _REFRESH_TOKEN_PATH,
    secure: bool = True,
):
    response.set_cookie(
        key=cookie_name,
        value=refresh_token,
        max_age=max_age,
        path=path,
        secure=secure,
        httponly=True,
        samesite="lax",
    )


def clear_refresh_token_cookie(
    response: Response,
    cookie_name: str = _REFRESH_TOKEN_COOKIE_NAME,
    path: str = _REFRESH_TOKEN_PATH,
):
    response.delete_cookie(key=cookie_name, path=path)
