from fastapi import APIRouter

router = APIRouter()


@router.get(
    path="/ping",
    summary="ping",
)
def ping():
    return "pong"
