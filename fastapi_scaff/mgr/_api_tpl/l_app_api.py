from fastapi import APIRouter, Depends, Query

from app.core.responses import Responses, response_docs
from app.services.tpl import (
    TplList,
    TplSvc,
    get_tpl_svc,
)

# -------------------- 请根据自身需求修改 --------------------

router = APIRouter()


@router.get(
    path="/tpls",
    summary="list",
    responses=response_docs(
        data={
            "items": [
                {
                    "id": "str",
                }
            ],
            "total": "int",
        }
    ),
)
async def list_tpl(
    req: TplList = Query(...),
    tpl_svc: TplSvc = Depends(get_tpl_svc),
    # current_user: JWTUser = Depends(get_current_user),  # TODO: 认证
):
    data = await tpl_svc.list_tpl(req)
    return Responses.success(data=data)
