from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.responses import Responses, response_docs

# -------------------- 请根据自身需求修改 --------------------

router = APIRouter()


class TplList(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=200)


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
    # TODO: 业务逻辑
    data = {
        "items": [],
        "total": 0,
    }
    return Responses.success(data=data)
