import logging

from app_celery.producer import celery_app
from app_celery.producer.registry import AllTasks

logger = logging.getLogger(__name__)


def publish(
    task_label: str,
    task_args: tuple = None,
    task_kwargs: dict = None,
    task_id: str = None,
    **task_options,
) -> str:
    """发布任务"""
    if task_label not in AllTasks:
        raise ValueError(f"UNKNOWN TASK: {task_label}")
    task_params = AllTasks[task_label]
    task_options_merged = task_params.options or {}
    task_options_merged.update(task_options)
    result = celery_app.send_task(
        name=task_params.name,
        args=task_args,
        kwargs=task_kwargs,
        task_id=task_id,
        queue=task_params.queue,  # enforced queue consistency
        **task_options_merged,
    )
    logger.info(f"PUBLISH TASK: {task_params.name} | ID={result.id} | QUEUE={task_params.queue}")
    return result.id
