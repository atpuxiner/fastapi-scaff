"""
初始化
"""

import logging
from functools import cached_property

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from toollib.guid import SnowFlake
from toollib.rediscli import RedisCli
from toollib.utils import Singleton

from app.core._conf import Config, init_config
from app.core._db import init_db_async_session
from app.core._log import init_logger
from app.core._redis import init_redis_cli
from app.core._snow import init_snow_cli

logger = logging.getLogger(__name__)


class G(metaclass=Singleton):
    """
    全局变量
    """

    _required_properties = (
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
    def logger(self):
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
    def db_async_session(self) -> async_sessionmaker[AsyncSession]:
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

    def setup(self, force: bool = False, required_properties: tuple | None = None):
        if force or not self._initialized:
            props = required_properties or self._required_properties or ()
            if force:
                for prop in props:
                    self.__dict__.pop(prop, None)  # type: ignore
            for prop_name in props:
                if hasattr(self, prop_name):
                    getattr(self, prop_name)
                else:
                    logger.warning(f"{prop_name} not found")
            self._initialized = True


g = G()
