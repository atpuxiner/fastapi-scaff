"""
初始化
"""
import sys
import threading
from datetime import datetime
from functools import cached_property

from loguru._logger import Logger  # noqa
from sqlalchemy.orm import sessionmaker, scoped_session
from toollib.guid import SnowFlake
from toollib.rediser import RedisCli
from toollib.utils import Singleton

from app.initializer._conf import Config, init_config
from app.initializer._db import init_db_session, init_db_async_session
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
        'config',
        'logger',
        'redis_cli',
        'snow_cli',
        # 'db_session',
        'db_async_session',
    ]

    def __init__(self):
        self._initialized = False

    @cached_property
    def config(self) -> Config:
        return init_config()

    @cached_property
    def logger(self) -> Logger:
        return init_logger(
            debug=self.config.app_debug,
            log_dir=self.config.app_log_dir,
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
            redis_cli=self.redis_cli,
            datacenter_id=self.config.snow_datacenter_id,
        )

    @cached_property
    def db_session(self) -> scoped_session:
        return init_db_session(
            db_url=self.config.db_url,
            db_echo=self.config.app_debug,
            is_create_tables=True,
        )

    @cached_property
    def db_async_session(self) -> sessionmaker:
        return init_db_async_session(
            db_url=self.config.db_async_url,
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
                        sys.stderr.write(
                            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]} "
                            f"Warning initializer "
                            f"{prop_name} not found"
                            f"\n"
                        )
                self._initialized = True


g = G()
