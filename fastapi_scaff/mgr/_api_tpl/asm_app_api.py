from fastapi import APIRouter
from loguru import logger

from app.api.responses import Responses, response_docs
from app.api.status import Status
from app.services.tpl import (
    TplDetailSvc,
)

router = APIRouter()


@router.get(
    path="/tpl/{tpl_id}",
    summary="tplDetail",
    responses=response_docs(
        model=TplDetailSvc,
    ),
)
async def detail(
        tpl_id: str,
        # TODO: 认证
):
    try:
        tpl_svc = TplDetailSvc(id=tpl_id)
        data = await tpl_svc.detail()
        if not data:
            return Responses.failure(status=Status.RECORD_NOT_EXIST_ERROR)
    except Exception as e:
        msg = "tplDetail操作异常"
        logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data=data)
