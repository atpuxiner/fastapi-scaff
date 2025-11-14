from fastapi import APIRouter

from app.api.responses import Responses, response_docs
from app.api.status import Status
from app.initializer import g

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
        if not data:
            return Responses.failure(status=Status.RECORD_NOT_EXIST_ERROR)
    except Exception as e:
        msg = "tplDetail操作异常"
        g.logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data=data)
