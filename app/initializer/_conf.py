import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from toollib.utils import get_cls_attrs, parse_variable

from app import APP_DIR

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
    snow_datacenter_id: int = None
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
    redis_host: str = None
    redis_port: int = None
    redis_db: int = None
    redis_password: str = None
    redis_max_connections: int = None

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


def init_config() -> Config:
    return Config().setup()
