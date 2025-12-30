import os
from pathlib import Path

from toollib.utils import ConfModel, FrozenVar

_APP_DIR = Path(__file__).absolute().parent
_CONFIG_DIR = _APP_DIR.parent.joinpath("config")

dotenv_path = _CONFIG_DIR.joinpath(".env")
if os.environ.setdefault("app_env", "dev") == "prod":  # 生产环境不加载.env（请根据自身需求修改）
    dotenv_path = None
yaml_path = _CONFIG_DIR.joinpath(f"app_{os.environ.get('app_env', 'dev')}.yaml")


class Config(ConfModel):
    """配置"""
    app_dir: FrozenVar[Path] = _APP_DIR
    # #
    app_env: str = "dev"
    yaml_path: Path = yaml_path
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


config = Config(
    dotenv_path=dotenv_path,
    yaml_path=yaml_path,
)
