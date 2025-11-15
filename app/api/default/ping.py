from fastapi import APIRouter

router = APIRouter()


@router.get(
    path="/ping",
    summary="ping",
)
async def ping():
    return "pong"
