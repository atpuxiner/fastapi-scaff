from fastapi import APIRouter

from app.api.responses import Responses, response_docs

# -------------------- 请根据自身需求修改 --------------------

router = APIRouter()


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
    # TODO: 业务逻辑
    data = {
        "items": [],
        "total": 0,
    }
    return Responses.success(data=data)
