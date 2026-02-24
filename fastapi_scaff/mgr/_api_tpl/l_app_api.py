from fastapi import APIRouter

from app.api.responses import Responses, response_docs
from app.services.tpl import (
    TplSvc,
    TplList,
)

router = APIRouter()

tpl_svc = TplSvc()


@router.get(
    path="/tpls",
    summary="list",
    responses=response_docs(data={
        "items": [{
            "id": "str",
        }],
        "total": "int",
    }),
)
async def list_tpl(
    page: int = 1,
    size: int = 10,
    # current_user: JWTUser = Depends(get_current_user),  # TODO: 认证
):
    req = TplList(
        page=page,
        size=size,
    )
    data = await tpl_svc.list_tpl(req)
    return Responses.success(data=data)
