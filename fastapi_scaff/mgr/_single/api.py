from fastapi import APIRouter, Security
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
from toollib.utils import now2timestr

from app.core import config

router = APIRouter()

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> str:
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )
    if api_key not in config.API_KEYS:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key


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
        "version": config.APP_VERSION,
        "timestamp": now2timestr(),
    }
