import secrets

_API_KEY_LENGTH = 45


def gen_api_key(prefix: str = "", length: int = _API_KEY_LENGTH) -> str:
    api_key = secrets.token_urlsafe(length)[:length]
    if prefix:
        return f"{prefix}_{api_key}"
    return api_key
