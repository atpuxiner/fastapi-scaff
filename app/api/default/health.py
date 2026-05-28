from fastapi import APIRouter

router = APIRouter()


@router.get(
    path="/health",
    summary="health",
)
async def health():
    raise Exception("测试异常")
    return "OK"
