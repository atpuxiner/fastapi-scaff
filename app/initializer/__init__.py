"""
初始化
"""

import threading
from functools import cached_property

from loguru import logger
from loguru._logger import Logger
from sqlalchemy.orm import sessionmaker
from toollib.guid import SnowFlake
from toollib.rediscli import RedisCli
from toollib.utils import Singleton

from app.initializer._conf import Config, init_config
from app.initializer._db import init_db_async_session
from app.initializer._log import init_logger
from app.initializer._redis import init_redis_cli
from app.initializer._snow import init_snow_cli


class G(metaclass=Singleton):
    """
    全局变量
    """

    _init_lock = threading.Lock()
    _init_properties = (
        "config",
        "logger",
        "redis_cli",
        "snow_cli",
        "db_async_session",
    )

    def __init__(self):
        self._initialized = False

    @cached_property
    def config(self) -> Config:
        return init_config()

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
            is_create_tables=True,
        )

    def setup(self):
        with self._init_lock:
            if not self._initialized:
                for prop_name in self._init_properties:
                    if hasattr(self, prop_name):
                        getattr(self, prop_name)
                    else:
                        logger.warning(f"{prop_name} not found")
                self._initialized = True


g = G()
