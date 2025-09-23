"""
消费者
"""
from pathlib import Path

from app_celery import make_celery


def autodiscover_task_modules(
        tasks_name: str = "tasks",
        tasks_module: str = "app_celery.consumer.tasks",
) -> list:
    here = Path(__file__).parent
    tasks_dir = here.joinpath(tasks_name)
    return [f"{tasks_module}.{p.stem}" for p in tasks_dir.rglob("*.py") if p.stem != "__init__"]


celery_app = make_celery(
    include=autodiscover_task_modules()
)
