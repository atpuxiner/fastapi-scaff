import os
from contextvars import ContextVar
from pathlib import Path

from toollib.utils import ConfLoader

_APP_DIR = Path(__file__).absolute().parent
_CONFIG_DIR = _APP_DIR.parent.joinpath("config")

dotenv_path = _CONFIG_DIR.joinpath(".env")
if os.environ.setdefault("app_env", "dev") == "prod":  # 生产环境不加载.env（请根据自身需求修改）
    dotenv_path = None
yaml_path = _CONFIG_DIR.joinpath(f"app_{os.environ.get('app_env', 'dev')}.yaml")


class Config(ConfLoader):
    """配置"""
    app_dir: Path = _APP_DIR
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


config = Config(
    dotenv_path=dotenv_path,
    yaml_path=yaml_path,
)
config.load()
request_id_var: ContextVar[str] = ContextVar("request_id", default="N/A")
