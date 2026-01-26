import secrets

_API_KEY_LENGTH = 45


def gen_api_key(prefix: str = "", length: int = _API_KEY_LENGTH) -> str:
    api_key = secrets.token_urlsafe(length)[:length]
    if prefix:
        return f"{prefix}_{api_key}"
    return api_key


if __name__ == '__main__':
    num = 2
    print(",".join([gen_api_key() for _ in range(num)]))
