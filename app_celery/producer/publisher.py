import logging

from app_celery.producer import celery_app
from app_celery.producer.registry import AllTasks

logger = logging.getLogger(__name__)


def publish(task_label: str, *args, **kwargs):
    """发布任务"""
    if task_label not in AllTasks:
        raise ValueError(f"UNKNOWN TASK: {task_label}")
    task_params = AllTasks[task_label]
    result = celery_app.send_task(
        name=task_params.name,
        queue=task_params.queue,
        args=args,
        kwargs=kwargs,
        **task_params.options,
    )
    logger.info(f"PUBLISH TASK: {task_label} | ID={result.id} | QUEUE={task_params.queue}")
    return result.id
