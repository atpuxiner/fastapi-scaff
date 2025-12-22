import os
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
    # #
    celery_broker_url: str
    celery_backend_url: str
    celery_timezone: str = "Asia/Shanghai"
    celery_enable_utc: bool = True
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    celery_task_ignore_result: bool = False
    celery_result_expire: int = 86400
    celery_task_track_started: bool = True
    celery_worker_concurrency: int = 8
    celery_worker_prefetch_multiplier: int = 2
    celery_worker_max_tasks_per_child: int = 100
    celery_broker_connection_retry_on_startup: bool = True
    celery_task_reject_on_worker_lost: bool = True


config = Config(yaml_path=app_yaml)
config.setup()
