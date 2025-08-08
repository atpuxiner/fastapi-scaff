import traceback

from fastapi import APIRouter, Depends

from app.api.response import Response, response_docs
from app.api.status import Status
from app.initializer import g
from app.middleware.auth import JWTUser, get_current_user

tpl_router = APIRouter()


@tpl_router.get(
    path="/tpl/{tpl_id}",
    summary="tplDetail",
    responses=response_docs(),
)
async def detail(
        tpl_id: str,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        data = {}  # TODO: 待处理
        if not data:
            return Response.failure(msg="未匹配到记录", status=Status.RECORD_NOT_EXIST_ERROR)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="tplDetail失败", error=e)
    return Response.success(data=data)
