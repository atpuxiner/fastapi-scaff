from fastapi import APIRouter

from app_celery.producer.publisher import publish

router = APIRouter()


@router.get(
    path="/aping",
    summary="aping",
)
def ping():
    publish("aping", text="这是一个测试任务")
    return "apong"
