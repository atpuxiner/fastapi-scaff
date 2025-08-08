import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from toollib.utils import get_cls_attrs, parse_variable

from app import APP_DIR

_CONFIG_DIR = APP_DIR.parent.joinpath("config")

load_dotenv(dotenv_path=os.environ.setdefault(
    key="envpath",
    value=str(_CONFIG_DIR.joinpath(".env")))
)
# #
appyaml = Path(
    os.environ.get("appyaml") or
    _CONFIG_DIR.joinpath(f"app_{os.environ.setdefault(key='appenv', value='dev')}.yaml")
)
if not appyaml.is_file():
    raise RuntimeError(f"配置文件不存在：{appyaml}")


class EnvConfig:
    """env配置"""
    snow_datacenter_id: int = None

    def setattr_from_env(self):
        cls_attrs = get_cls_attrs(EnvConfig)
        for k, item in cls_attrs.items():
            v_type, v = item
            if callable(v_type):
                v = parse_variable(k=k, v_type=v_type, v_from=os.environ, default=v)
            setattr(self, k, v)


class Config(EnvConfig):
    """配置"""
    yamlname: str = appyaml.name
    #
    appname: str = "xApp"
    appversion: str = "1.0.0"
    debug: bool = True
    log_dir: str = "./log"
    is_disable_docs: bool = True
    # #
    redis_host: str = None
    redis_port: int = None
    redis_db: int = None
    redis_password: str = None
    redis_max_connections: int = None
    db_url: str = None
    db_async_url: str = None

    def setup(self):
        self.setattr_from_env()
        self.setattr_from_yaml()
        return self

    def setattr_from_yaml(self):
        cls_attrs = get_cls_attrs(Config)
        for k, item in cls_attrs.items():
            v_type, v = item
            if callable(v_type):
                v = parse_variable(k=k, v_type=v_type, v_from=self.load_yaml(), default=v)
            setattr(self, k, v)

    @staticmethod
    def load_yaml() -> dict:
        with open(appyaml, mode="r", encoding="utf-8") as file:
            return yaml.safe_load(file)


def init_config() -> Config:
    return Config().setup()
