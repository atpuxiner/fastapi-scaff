from fastapi import APIRouter
from loguru import logger

from app.api.responses import Responses, response_docs

router = APIRouter()


@router.get(
    path="/tpl/{tpl_id}",
    summary="tplDetail",
    responses=response_docs(),
)
async def detail(
        tpl_id: str,
        # TODO: 认证
):
    try:
        data = {}  # TODO: 数据
    except Exception as e:
        msg = "tplDetail操作异常"
        logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data=data)
