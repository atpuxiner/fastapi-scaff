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
    yaml_name: str = app_yaml.name
    #
    celery_broker_url: str
    celery_backend_url: str
    celery_timezone: str = "Asia/Shanghai"
    celery_enable_utc: bool = True
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    celery_task_ignore_result: bool = False
    celery_result_expire: int = 7200
    celery_task_track_started: bool = True
    celery_worker_concurrency: int = 8
    celery_worker_prefetch_multiplier: int = 2
    celery_broker_connection_retry_on_startup: bool = True
    celery_task_reject_on_worker_lost: bool = True

    def setup(self):
        self.setattr_from_env_or_yaml()
        return self

    def setattr_from_env_or_yaml(self):
        cls_attrs = get_cls_attrs(Config)
        for k, item in cls_attrs.items():
            v_type, v = item
            if callable(v_type):
                if k in os.environ:  # 优先环境变量
                    v = parse_variable(k=k, v_type=v_type, v_from=os.environ, default=v)
                else:
                    v = parse_variable(k=k, v_type=v_type, v_from=self.load_yaml(), default=v)
            setattr(self, k, v)

    def load_yaml(self, reload: bool = False) -> dict:
        if self._yaml_conf and not reload:
            return self._yaml_conf
        with open(app_yaml, mode="r", encoding="utf-8") as file:
            self._yaml_conf = yaml.load(file, Loader=yaml.FullLoader)
            return self._yaml_conf


config = Config().setup()
