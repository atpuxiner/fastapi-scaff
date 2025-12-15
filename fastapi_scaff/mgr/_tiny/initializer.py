"""
初始化
"""
import os
import threading
from contextvars import ContextVar
from functools import cached_property
from pathlib import Path

import yaml
from dotenv import load_dotenv
from loguru import logger
from loguru._logger import Logger  # noqa
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import scoped_session, sessionmaker
from toollib import logu
from toollib.utils import Singleton, get_cls_attrs, parse_variable

from app import APP_DIR

__all__ = [
    "g",
    "request_id_var",
]

_CONFIG_DIR = APP_DIR.parent.joinpath("config")

load_dotenv(dotenv_path=os.environ.setdefault(
    key="env_path",
    value=str(_CONFIG_DIR.joinpath(".env")))
)
# #
app_yaml = Path(
    os.environ.get("app_yaml") or
    _CONFIG_DIR.joinpath(f"app_{os.environ.setdefault(key='app_env', value='dev')}.yaml")
)
if not app_yaml.is_file():
    raise RuntimeError(f"配置文件不存在：{app_yaml}")


class Config:
    """配置"""
    _yaml_conf: dict = None
    app_dir: Path = APP_DIR
    # #
    app_env: str = "dev"
    app_yaml: Path = app_yaml
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
    db_url: str = None
    db_async_url: str = None

    def setup(self):
        for k, item in get_cls_attrs(Config).items():
            v_type, v = item
            if callable(v_type):
                if k in os.environ:  # 优先环境变量
                    v = parse_variable(k=k, v_type=v_type, v_from=os.environ, default=v)
                else:
                    v = parse_variable(k=k, v_type=v_type, v_from=self.load_yaml(), default=v)
            setattr(self, k, v)
        return self

    def load_yaml(self, reload: bool = False) -> dict:
        if self._yaml_conf and not reload:
            return self._yaml_conf
        with open(app_yaml, mode="r", encoding="utf-8") as file:
            self._yaml_conf = yaml.load(file, Loader=yaml.FullLoader)
            return self._yaml_conf


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
        db_url: str,
        db_echo: bool,
        db_pool_size: int = 10,
        db_max_overflow: int = 5,
        db_pool_recycle: int = 3600,
) -> scoped_session:
    db_echo = db_echo or False
    kwargs = {
        "pool_size": db_pool_size,
        "max_overflow": db_max_overflow,
        "pool_recycle": db_pool_recycle,
    }
    if db_url.startswith("sqlite"):
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
        db_url: str,
        db_echo: bool,
        db_pool_size: int = 10,
        db_max_overflow: int = 5,
        db_pool_recycle: int = 3600,
) -> sessionmaker:
    db_echo = db_echo or False
    kwargs = {
        "pool_size": db_pool_size,
        "max_overflow": db_max_overflow,
        "pool_recycle": db_pool_recycle,
    }
    if db_url.startswith("sqlite"):
        kwargs = {}
    async_engine = create_async_engine(
        url=db_url,
        echo=db_echo,
        pool_pre_ping=True,
        **kwargs,
    )
    db_async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)  # noqa
    return db_async_session


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
        return Config().setup()

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
            db_url=self.config.db_url,
            db_echo=self.config.app_debug,
        )

    @cached_property
    def db_async_session(self) -> sessionmaker:
        return init_db_async_session(
            db_url=self.config.db_async_url,
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
