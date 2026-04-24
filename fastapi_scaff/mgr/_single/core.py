import os
from contextvars import ContextVar
from pathlib import Path

from dotenv import load_dotenv
from toollib.utils import ConfModel, FrozenVar

from app import APP_DIR

_CONFIG_DIR = APP_DIR.parent.joinpath("config")
if os.environ.get("APP_ENV") != "prod":  # 是否加载.env（请根据自身需求修改）
    DOTENV_PATH = _CONFIG_DIR.joinpath(".env")
    load_dotenv(DOTENV_PATH)
YAML_PATH = _CONFIG_DIR.joinpath(f"app_{os.environ.get('APP_ENV', 'dev')}.yaml")


class Config(ConfModel):
    """配置"""

    APP_DIR: FrozenVar[Path] = APP_DIR
    # #
    APP_ENV: str = "dev"
    YAML_PATH: Path = YAML_PATH
    API_KEYS: list = []
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


config = Config(
    yaml_path=YAML_PATH,
    prefer_env_path=True,
    prefer_env_attr=True,
)
request_id_var: ContextVar[str] = ContextVar("request_id", default="N/A")
