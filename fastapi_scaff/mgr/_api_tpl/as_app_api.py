import traceback

from fastapi import APIRouter, Depends
from starlette.requests import Request

from app.api.response import Response, response_docs
from app.service.tpl import (
    TplDetailSvc,
)
from app.api.status import Status
from app.initializer import g
from app.middleware.auth import JWTUser, get_current_user

router = APIRouter()


@router.get(
    path="/tpl/{tpl_id}",
    summary="tplDetail",
    responses=response_docs(
        model=TplDetailSvc,
    ),
)
async def detail(
        request: Request,
        tpl_id: str,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        tpl_svc = TplDetailSvc(id=tpl_id)
        data = await tpl_svc.detail()
        if not data:
            return Response.failure(status=Status.RECORD_NOT_EXIST_ERROR, request=request)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="tplDetail失败", error=e, request=request)
    return Response.success(data=data, request=request)
