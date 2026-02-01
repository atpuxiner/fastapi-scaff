"""
初始化
"""
import threading
from functools import cached_property

from loguru import logger
from loguru._logger import Logger  # noqa
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
    _initialized = False
    _init_lock = threading.Lock()
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
        return init_config()

    @cached_property
    def logger(self) -> Logger:
        return init_logger(
            level="DEBUG" if self.config.app_debug else "INFO",
            serialize=self.config.app_log_serialize,
            outdir=self.config.app_log_outdir,
        )

    @cached_property
    def redis_cli(self) -> RedisCli:
        return init_redis_cli(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            password=self.config.redis_password,
            max_connections=self.config.redis_max_connections,
        )

    @cached_property
    def snow_cli(self) -> SnowFlake:
        return init_snow_cli(
            redis_cli=getattr(self, "redis_cli", None),
            datacenter_id=self.config.snow_datacenter_id,
        )

    @cached_property
    def db_async_session(self) -> sessionmaker:
        return init_db_async_session(
            db_drivername=self.config.db_async_drivername,
            db_database=self.config.db_database,
            db_username=self.config.db_username,
            db_password=self.config.db_password,
            db_host=self.config.db_host,
            db_port=self.config.db_port,
            db_charset=self.config.db_charset,
            db_echo=self.config.app_debug,
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
