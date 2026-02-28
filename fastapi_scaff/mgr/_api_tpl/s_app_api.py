from fastapi import APIRouter, Depends, Query

from app.api.dependencies import JWTUser, get_current_user
from app.api.responses import Responses, response_docs
from app.models.tpl import (
    TplList,
    TplCreate,
    TplUpdate,
)
from app.services.tpl import TplSvc

# -------------------- 请根据自身需求修改 --------------------

router = APIRouter()

tpl_svc = TplSvc()


@router.get(
    path="/tpls",
    summary="list",
    responses=response_docs(data={
        "items": [{
            "id": "str",
            "name": "str",
            "created_at": "int",
            "updated_at": "int",
        }],
        "total": "int",
    }),
)
async def list_tpl(
    req: TplList = Query(...),
    current_user: JWTUser = Depends(get_current_user),
):
    data = await tpl_svc.list_tpl(req)
    return Responses.success(data=data)


@router.post(
    path="/tpls",
    summary="create",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def create_tpl(
    req: TplCreate,
    current_user: JWTUser = Depends(get_current_user),
):
    data = await tpl_svc.create_tpl(req)
    return Responses.success(data=data)


@router.get(
    path="/tpls/{tpl_id}",
    summary="get",
    responses=response_docs(data={
        "id": "str",
        "name": "str",
        "created_at": "int",
        "updated_at": "int",
    }),
)
async def get_tpl(
    tpl_id: str,
    current_user: JWTUser = Depends(get_current_user),  # 认证
):
    data = await tpl_svc.get_tpl(tpl_id)
    return Responses.success(data=data)


@router.delete(
    path="/tpls/{tpl_id}",
    summary="delete",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def delete_tpl(
    tpl_id: str,
    current_user: JWTUser = Depends(get_current_user),
):
    data = await tpl_svc.delete_tpl(tpl_id)
    return Responses.success(data=data)


@router.put(
    path="/tpls/{tpl_id}",
    summary="update",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def update_tpl(
    tpl_id: str,
    req: TplUpdate,
    current_user: JWTUser = Depends(get_current_user),
):
    data = await tpl_svc.update_tpl(req, tpl_id=tpl_id)
    return Responses.success(data=data)
