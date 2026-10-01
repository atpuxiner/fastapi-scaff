from datetime import UTC, datetime

from fastapi import APIRouter

from app.core import g

router = APIRouter()


@router.get(
    path="/health",
    summary="health",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "version": "1.0.0",
                        "timestamp": "2026-01-01T01:01:01.000+00:00",
                    }
                }
            },
        }
    },
)
async def health():
    return {
        "status": "ok",
        "version": g.config.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
    }
