from fastapi import APIRouter

from app_celery.producer.publisher import publish

router = APIRouter()


@router.get(
    path="/aping",
    summary="aping",
)
def ping():
    task_id = publish("ping")
    return f"pong > {task_id}"
