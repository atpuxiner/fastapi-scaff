from fastapi import APIRouter

from app.api.responses import Responses, response_docs
from app.services.tpl import (
    TplListSvc,
)

router = APIRouter()


@router.get(
    path="/tpls",
    summary="list",
    responses=response_docs(
        model=TplListSvc,
    ),
)
async def list_tpl(
        # current_user: JWTUser = Depends(get_current_user),  # TODO: 认证
):
    tpl_svc = TplListSvc()
    data = await tpl_svc.list_tpl()
    return Responses.success(data=data)
