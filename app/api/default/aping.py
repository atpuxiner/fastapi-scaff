from fastapi import APIRouter

from app_celery.producer import publisher

router = APIRouter()


@router.get(
    path="/aping",
    summary="aping",
)
def ping():
    task_id = publisher.publish("ping")
    return f"pong > {task_id}"
