"""
消费者
"""
import re
from pathlib import Path

from app_celery import make_celery


def autodiscover_task_modules(
    task_name: str = "tasks",
    task_module: str = "app_celery.consumer.tasks",
) -> list:
    """
    自动发现任务模块
    - 可在模块中加入`_active = False`来取消激活
    """
    task_modules = []
    active_pat = re.compile(r"^_active\s*=\s*False\s*(?:#.*)?$", re.MULTILINE)
    for p in Path(__file__).parent.joinpath(task_name).rglob("*.py"):
        if p.stem == "__init__":
            continue
        if active_pat.search(p.read_text(encoding="utf-8")):
            continue
        task_modules.append(f"{task_module}.{p.stem}")
    return task_modules


celery_app = make_celery(
    include=autodiscover_task_modules()
)
