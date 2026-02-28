from fastapi import APIRouter, Query

from app.api.responses import Responses, response_docs
from app.services.tpl import (
    TplSvc,
    TplList,
)

# -------------------- 请根据自身需求修改 --------------------

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
    req: TplList = Query(...),
    # current_user: JWTUser = Depends(get_current_user),  # TODO: 认证
):
    data = await tpl_svc.list_tpl(req)
    return Responses.success(data=data)
