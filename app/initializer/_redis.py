from toollib.rediser import RedisClient


def init_redis_client(
        host: str,
        port: int,
        db: int,
        password: str = None,
        max_connections: int = None,
        **kwargs,
) -> RedisClient:
    if not host:
        return RedisClient()
    return RedisClient(
        host=host,
        port=port,
        db=db,
        password=password,
        max_connections=max_connections,
        **kwargs,
    )
