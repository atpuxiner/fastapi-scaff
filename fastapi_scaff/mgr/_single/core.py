import os
from contextvars import ContextVar
from pathlib import Path

from dotenv import load_dotenv
from toollib.utils import YamlConfig

_APP_DIR = Path(__file__).absolute().parent
_CONFIG_DIR = _APP_DIR.parent.joinpath("config")

if os.environ.get("app_env", "dev") != "prod":
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


class Config(YamlConfig):
    """配置"""
    app_dir: Path = _APP_DIR
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


config = Config(yaml_path=app_yaml)
config.setup()
request_id_var: ContextVar[str] = ContextVar("request_id", default="N/A")
