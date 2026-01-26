from fastapi import APIRouter, Security
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core import config

router = APIRouter()

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_api_key(
        api_key: str | None = Security(_API_KEY_HEADER)
) -> str:
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    if api_key not in config.api_keys:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key


@router.get(
    path="/api/ping",
    summary="ping",
)
async def ping():
    return "pong"
