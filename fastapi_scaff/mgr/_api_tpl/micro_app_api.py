import traceback

from fastapi import APIRouter
from starlette.requests import Request

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
        request: Request,
        tpl_id: str,
        # TODO: 认证
):
    try:
        data = {}  # TODO: 数据
        if not data:
            return Responses.failure(status=Status.RECORD_NOT_EXIST_ERROR, request=request)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Responses.failure(msg="tplDetail失败", error=e, request=request)
    return Responses.success(data=data, request=request)
