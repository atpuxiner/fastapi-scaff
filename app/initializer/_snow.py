import os

from loguru import logger
from toollib.guid import SnowFlake
from toollib.rediser import RedisClient
from toollib.utils import localip

_CACHE_KEY_SNOW_WORKER_ID_INCR = "config:snow_worker_id_incr"
_CACHE_KEY_SNOW_DATACENTER_ID_INCR = "config:snow_datacenter_id_incr"
_CACHE_EXPIRE_SNOW = 120


def init_snow_client(
        redis_client: RedisClient,
        datacenter_id: int = None,
        to_str: bool = True,
) -> SnowFlake:  # 建议：采用服务的方式调用api获取
    if datacenter_id is None:
        datacenter_id = _snow_incr(redis_client, _CACHE_KEY_SNOW_DATACENTER_ID_INCR, _CACHE_EXPIRE_SNOW)
        if datacenter_id is None:
            local_ip = localip()
            if local_ip:
                ip_parts = list(map(int, local_ip.split('.')))
                ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
                datacenter_id = ip_int % 32
    worker_id = _snow_incr(redis_client, _CACHE_KEY_SNOW_WORKER_ID_INCR, _CACHE_EXPIRE_SNOW)
    if worker_id is None:
        worker_id = os.getpid() % 32
    return SnowFlake(worker_id=worker_id, datacenter_id=datacenter_id, to_str=to_str)


def _snow_incr(redis_client, cache_key: str, cache_expire: int):
    incr = None
    try:
        with redis_client.connection() as r:
            resp = r.ping()
            if resp:
                lua_script = """
                    if redis.call('exists', KEYS[1]) == 1 then
                        redis.call('expire', KEYS[1], ARGV[1])
                        return redis.call('incr', KEYS[1])
                    else
                        redis.call('set', KEYS[1], 0)
                        redis.call('expire', KEYS[1], ARGV[1])
                        return 0
                    end
                    """
                incr = r.eval(lua_script, 1, cache_key, cache_expire)
    except Exception as e:
        logger.warning(f"snow初始化id将采用本地方式，由于（{e}）")
    return incr
