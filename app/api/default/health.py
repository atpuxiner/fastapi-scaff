from fastapi import APIRouter
from toollib.utils import now2timestr

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
                        "timestamp": "2026-01-01 01:01:01",
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
        "timestamp": now2timestr(),
    }
