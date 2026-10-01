from datetime import UTC, datetime

from fastapi import APIRouter

from app.core import g
from app_celery.producer import publisher

router = APIRouter()


@router.get(
    path="/ahealth",
    summary="ahealth",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "xxx",
                        "status": "ok",
                        "version": "1.0.0",
                        "timestamp": "2026-01-01T01:01:01.000+00:00",
                    }
                }
            },
        }
    },
)
async def ahealth():
    task_id = publisher.publish("health")
    return {
        "task_id": task_id,
        "status": "ok",
        "version": g.config.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
    }
