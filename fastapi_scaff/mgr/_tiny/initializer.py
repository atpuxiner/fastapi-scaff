"""
初始化
"""
import os
import threading
from contextvars import ContextVar
from functools import cached_property
from pathlib import Path

from loguru import logger
from loguru._logger import Logger  # noqa
from sqlalchemy import URL, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import scoped_session, sessionmaker
from toollib import logu
from toollib.utils import ConfModel, FrozenVar, Singleton

from app import APP_DIR

__all__ = [
    "g",
    "request_id_var",
]

_CONFIG_DIR = APP_DIR.parent.joinpath("config")

dotenv_path = _CONFIG_DIR.joinpath(".env")
if os.environ.setdefault("app_env", "dev") == "prod":  # 生产环境不加载.env（请根据自身需求修改）
    dotenv_path = None
yaml_path = _CONFIG_DIR.joinpath(f"app_{os.environ.get('app_env', 'dev')}.yaml")


class Config(ConfModel):
    """配置"""
    app_dir: FrozenVar[Path] = APP_DIR
    # #
    app_env: str = "dev"
    yaml_path: Path = yaml_path
    api_keys: list = []
    # #
    app_title: str = "xApp"
    app_summary: str = "xxApp"
    app_description: str = "xxxApp"
    app_version: str = "1.0.0"
    app_debug: bool = True
    app_log_serialize: bool = False
    app_log_basedir: str = "./logs"
    app_disable_docs: bool = False
    app_allow_credentials: bool = True
    app_allow_origins: list = ["*"]
    app_allow_methods: list = ["*"]
    app_allow_headers: list = ["*"]
    # #
    db_drivername: str
    db_async_drivername: str
    db_database: str
    db_username: str = None
    db_password: str = None
    db_host: str = None
    db_port: int = None
    db_charset: str = None


def init_logger(
        level: str,
        serialize: bool = False,
        basedir: str = None,
) -> Logger:
    enable_console, enable_file = True, True
    if os.getenv("app_env") == "prod":
        enable_console, enable_file = False, True  # 按需调整
    _logger = logu.init_logger(
        level=level,
        request_id_var=request_id_var,
        serialize=serialize,
        enable_console=enable_console,
        enable_file=enable_file,
        basedir=basedir,
    )
    # _logger.add 可添加其他 handler
    return _logger


def init_db_session(
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
) -> scoped_session:
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
    engine = create_engine(
        url=db_url,
        echo=db_echo,
        pool_pre_ping=True,
        **kwargs,
    )
    db_session = sessionmaker(engine, expire_on_commit=False)
    return scoped_session(db_session)


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
    db_async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)  # noqa
    return db_async_session


def make_db_url(
        drivername: str,
        database: str,
        username: str = None,
        password: str = None,
        host: str = None,
        port: int = None,
        query: dict = None,
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
    _initialized = False
    _init_lock = threading.Lock()
    _init_properties = [
        'config',
        'logger',
        # 'db_session',
        'db_async_session',
    ]

    def __init__(self):
        self._initialized = False

    @cached_property
    def config(self) -> Config:
        return Config(
            dotenv_path=dotenv_path,
            yaml_path=yaml_path,
        )

    @cached_property
    def logger(self) -> Logger:
        return init_logger(
            level="DEBUG" if self.config.app_debug else "INFO",
            serialize=self.config.app_log_serialize,
            basedir=self.config.app_log_basedir,
        )

    @cached_property
    def db_session(self) -> scoped_session:
        return init_db_session(
            db_drivername=self.config.db_drivername,
            db_database=self.config.db_database,
            db_username=self.config.db_username,
            db_password=self.config.db_password,
            db_host=self.config.db_host,
            db_port=self.config.db_port,
            db_charset=self.config.db_charset,
            db_echo=self.config.app_debug,
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
request_id_var: ContextVar[str] = ContextVar("request_id", default="N/A")
