"""
初始化
"""
from loguru._logger import Logger  # noqa
from sqlalchemy.orm import sessionmaker, scoped_session
from toollib.guid import SnowFlake
from toollib.rediser import RedisCli
from toollib.utils import Singleton

from app.initializer._conf import init_config
from app.initializer._db import init_db_session, init_db_async_session
from app.initializer._log import init_logger
from app.initializer._redis import init_redis_cli
from app.initializer._snow import init_snow_cli


class G(metaclass=Singleton):
    """
    全局变量
    """
    config = None
    logger: Logger = None
    redis_cli: RedisCli = None
    snow_cli: SnowFlake = None
    db_session: scoped_session = None
    db_async_session: sessionmaker = None

    def __getattribute__(self, name):
        try:
            value = super().__getattribute__(name)
        except AttributeError:
            value = None
        if value is None:
            getter_name = f"_get_{name}"
            getter_method = getattr(self.__class__, getter_name, None)
            if callable(getter_method):
                value = getter_method()
                setattr(self, name, value)
        return value

    @classmethod
    def _get_config(cls):
        if not cls.config:
            cls.config = init_config()
        return cls.config

    @classmethod
    def _get_logger(cls):
        if not cls.logger:
            cls.logger = init_logger(
                debug=cls.config.app_debug,
                log_dir=cls.config.app_log_dir,
            )
        return cls.logger

    @classmethod
    def _get_redis_cli(cls):
        if not cls.redis_cli:
            cls.redis_cli = init_redis_cli(
                host=cls.config.redis_host,
                port=cls.config.redis_port,
                db=cls.config.redis_db,
                password=cls.config.redis_password,
                max_connections=cls.config.redis_max_connections,
            )
        return cls.redis_cli

    @classmethod
    def _get_snow_cli(cls):
        if not cls.snow_cli:
            cls.snow_cli = init_snow_cli(
                redis_cli=cls.redis_cli,
                datacenter_id=cls.config.snow_datacenter_id,
            )
        return cls.snow_cli

    @classmethod
    def _get_db_session(cls):
        if not cls.db_session:
            cls.db_session = init_db_session(
                db_url=cls.config.db_url,
                db_echo=cls.config.app_debug,
            )
        return cls.db_session

    @classmethod
    def _get_db_async_session(cls):
        if not cls.db_async_session:
            cls.db_async_session = init_db_async_session(
                db_url=cls.config.db_async_url,
                db_echo=cls.config.app_debug,
            )
        return cls.db_async_session

    @classmethod
    def setup(cls):
        """
        初始化
        """
        cls._get_config()
        cls._get_logger()
        cls._get_redis_cli()
        cls._get_snow_cli()
        # cls._get_db_session()
        cls._get_db_async_session()


g = G()
