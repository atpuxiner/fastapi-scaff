from fastapi import APIRouter

from app_celery.producer import publisher

router = APIRouter()


@router.get(
    path="/ahealth",
    summary="ahealth",
)
async def ahealth():
    task_id = publisher.publish("health")
    return f"OK > {task_id}"
