"""
初始化
"""

import os
from contextvars import ContextVar
from functools import cached_property
from pathlib import Path

from loguru import logger
from loguru._logger import Logger
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from toollib import logu
from toollib.guid import SnowFlake
from toollib.rediscli import RedisCli
from toollib.utils import ConfModel, FrozenVar, Singleton, localip

from app import APP_DIR

__all__ = [
    "g",
    "request_id_var",
]

_CONFIG_DIR = APP_DIR.parent.joinpath("config")

DOTENV_PATH = _CONFIG_DIR.joinpath(".env")
if os.environ.setdefault("APP_ENV", "dev") == "prod":  # 生产环境不加载.env（请根据自身需求修改）
    DOTENV_PATH = None
YAML_PATH = _CONFIG_DIR.joinpath(f"app_{os.environ.get('APP_ENV', 'dev')}.yaml")


class Config(ConfModel):
    """配置"""

    APP_DIR: FrozenVar[Path] = APP_DIR
    # #
    APP_ENV: str = "dev"
    YAML_PATH: Path = YAML_PATH
    API_KEYS: list = []
    JWT_KEY: str = ""
    SNOW_DATACENTER_ID: int = None
    # #
    APP_TITLE: str = "xApp"
    APP_SUMMARY: str = "xxApp"
    APP_DESCRIPTION: str = "xxxApp"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = True
    APP_LOG_SERIALIZE: bool = False
    APP_LOG_OUTDIR: str = "./logs"
    APP_DISABLE_DOCS: bool = False
    APP_ALLOW_CREDENTIALS: bool = True
    APP_ALLOW_ORIGINS: list = ["*"]
    APP_ALLOW_METHODS: list = ["*"]
    APP_ALLOW_HEADERS: list = ["*"]
    # #
    DB_DRIVERNAME: str
    DB_ASYNC_DRIVERNAME: str
    DB_DATABASE: str
    DB_USERNAME: str = None
    DB_PASSWORD: str = None
    DB_HOST: str = None
    DB_PORT: int = None
    DB_CHARSET: str = None
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str = None
    REDIS_MAX_CONNECTIONS: int = None


def init_logger(
    level: str,
    serialize: bool = False,
    outdir: str | None = None,
) -> Logger:
    enable_console, enable_file = True, True
    if os.getenv("APP_ENV") == "prod":
        enable_console, enable_file = False, True  # 按需调整
    _logger = logu.init_logger(
        level=level,
        request_id_var=request_id_var,
        serialize=serialize,
        enable_console=enable_console,
        enable_file=enable_file,
        outdir=outdir,
    )
    # _logger.add 可添加其他 handler
    return _logger


def init_redis_cli(
    host: str,
    port: int,
    db: int,
    password: str | None = None,
    max_connections: int | None = None,
    **kwargs,
) -> RedisCli:
    return RedisCli(
        host=host,
        port=port,
        db=db,
        password=password,
        max_connections=max_connections,
        **kwargs,
    )


_CACHE_KEY_SNOW_WORKER_ID_INCR = "config:snow_worker_id_incr"
_CACHE_KEY_SNOW_DATACENTER_ID_INCR = "config:snow_datacenter_id_incr"
_CACHE_EXPIRE_SNOW = 120


def init_snow_cli(
    redis_cli=None,  # `from toollib.rediscli import RedisCli` 实例
    datacenter_id: int | None = None,
) -> SnowFlake:
    # 建议：采用服务的方式调用api获取
    if datacenter_id is None:
        datacenter_id = _snow_incr(redis_cli, _CACHE_KEY_SNOW_DATACENTER_ID_INCR, _CACHE_EXPIRE_SNOW)
        if datacenter_id is None:
            local_ip = localip()
            if local_ip:
                ip_parts = list(map(int, local_ip.split(".")))
                ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
                datacenter_id = ip_int % 32
    worker_id = _snow_incr(redis_cli, _CACHE_KEY_SNOW_WORKER_ID_INCR, _CACHE_EXPIRE_SNOW)
    if worker_id is None:
        worker_id = os.getpid() % 32
    return SnowFlake(worker_id=worker_id, datacenter_id=datacenter_id)


def _snow_incr(redis_cli, cache_key: str, cache_expire: int):
    incr = None
    if not redis_cli:
        return incr
    try:
        with redis_cli.connection() as r:
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


def init_db_async_session(
    db_drivername: str,
    db_database: str,
    db_username: str,
    db_password: str,
    db_host: str,
    db_port: int,
    db_charset: str,
    db_echo: bool,
    db_pool_size: int = 10,
    db_max_overflow: int = 5,
    db_pool_recycle: int = 3600,
) -> sessionmaker:
    db_url = make_db_url(
        drivername=db_drivername,
        database=db_database,
        username=db_username,
        password=db_password,
        host=db_host,
        port=db_port,
        query={
            "charset": db_charset,
        },
    )
    db_echo = db_echo or False
    kwargs = {
        "pool_size": db_pool_size,
        "max_overflow": db_max_overflow,
        "pool_recycle": db_pool_recycle,
    }
    if db_url.drivername.startswith("sqlite"):
        kwargs = {}
    async_engine = create_async_engine(
        url=db_url,
        echo=db_echo,
        pool_pre_ping=True,
        **kwargs,
    )
    db_async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore
    return db_async_session


def make_db_url(
    drivername: str,
    database: str,
    username: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: int | None = None,
    query: dict | None = None,
) -> URL:
    query = {k: v for k, v in query.items() if v} if query else {}
    return URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        query=query,
    )


class G(metaclass=Singleton):
    """
    全局变量
    """

    _init_properties = [
        "config",
        "logger",
        "redis_cli",
        "snow_cli",
        "db_async_session",
    ]

    def __init__(self):
        self._initialized = False

    @cached_property
    def config(self) -> Config:
        return Config(
            dotenv_path=DOTENV_PATH,
            yaml_path=YAML_PATH,
        )

    @cached_property
    def logger(self) -> Logger:
        return init_logger(
            level="DEBUG" if self.config.APP_DEBUG else "INFO",
            serialize=self.config.APP_LOG_SERIALIZE,
            outdir=self.config.APP_LOG_OUTDIR,
        )

    @cached_property
    def redis_cli(self) -> RedisCli:
        return init_redis_cli(
            host=self.config.REDIS_HOST,
            port=self.config.REDIS_PORT,
            db=self.config.REDIS_DB,
            password=self.config.REDIS_PASSWORD,
            max_connections=self.config.REDIS_MAX_CONNECTIONS,
        )

    @cached_property
    def snow_cli(self) -> SnowFlake:
        return init_snow_cli(
            redis_cli=getattr(self, "redis_cli", None),
            datacenter_id=self.config.SNOW_DATACENTER_ID,
        )

    @cached_property
    def db_async_session(self) -> sessionmaker:
        return init_db_async_session(
            db_drivername=self.config.DB_ASYNC_DRIVERNAME,
            db_database=self.config.DB_DATABASE,
            db_username=self.config.DB_USERNAME,
            db_password=self.config.DB_PASSWORD,
            db_host=self.config.DB_HOST,
            db_port=self.config.DB_PORT,
            db_charset=self.config.DB_CHARSET,
            db_echo=self.config.APP_DEBUG,
        )

    def setup(self, force: bool = False):
        if force or not self._initialized:
            if force:
                for prop in self._init_properties:
                    self.__dict__.pop(prop, None)  # type: ignore
            for prop_name in self._init_properties:
                if hasattr(self, prop_name):
                    getattr(self, prop_name)
                else:
                    logger.warning(f"{prop_name} not found")
            self._initialized = True


g = G()
request_id_var: ContextVar[str] = ContextVar("request_id", default="N/A")
