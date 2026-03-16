import os
from pathlib import Path

from toollib.utils import ConfModel, FrozenVar

_APP_DIR = Path(__file__).resolve().parent
_CONFIG_DIR = _APP_DIR.parent.joinpath("config")

DOTENV_PATH = _CONFIG_DIR.joinpath(".env")
if os.environ.setdefault("APP_ENV", "dev") == "prod":  # 生产环境不加载.env（请根据自身需求修改）
    DOTENV_PATH = None
YAML_PATH = _CONFIG_DIR.joinpath(f"app_{os.environ.get('APP_ENV', 'dev')}.yaml")


class Config(ConfModel):
    """配置"""

    APP_DIR: FrozenVar[Path] = _APP_DIR
    # #
    APP_ENV: str = "dev"
    YAML_PATH: Path = YAML_PATH
    # #
    CELERY_BROKER_URL: str
    CELERY_BACKEND_URL: str
    CELERY_TIMEZONE: str = "Asia/Shanghai"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TASK_IGNORE_RESULT: bool = False
    CELERY_RESULT_EXPIRE: int = 86400
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_WORKER_CONCURRENCY: int = 8
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 2
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 100
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP: bool = True
    CELERY_TASK_REJECT_ON_WORKER_LOST: bool = True


config = Config(
    dotenv_path=DOTENV_PATH,
    yaml_path=YAML_PATH,
)
