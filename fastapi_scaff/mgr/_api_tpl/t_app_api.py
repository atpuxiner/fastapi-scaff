from fastapi import APIRouter

from app.api.responses import Responses, response_docs

router = APIRouter()


@router.get(
    path="/tpls",
    summary="list",
    responses=response_docs(),
)
async def list_tpl(
        # current_user: JWTUser = Depends(get_current_user),  # TODO: 认证
):
    data = {}  # TODO: 数据
    return Responses.success(data=data)
