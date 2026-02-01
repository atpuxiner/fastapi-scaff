from fastapi import APIRouter, Depends

from app.api.dependencies import JWTUser, get_current_user
from app.api.responses import Responses, response_docs
from app.services.tpl import (
    TplListSvc,
    TplCreateSvc,
    TplGetSvc,
    TplDeleteSvc,
    TplUpdateSvc,
)

router = APIRouter()

# -------------------- 请根据自身需求修改 --------------------


@router.get(
    path="/tpls",
    summary="list",
    responses=response_docs(
        model=TplListSvc,
        is_listwrap=True,
        listwrap_key="items",
        listwrap_key_extra={
            "total": "int",
        },
    ),
)
async def list_tpl(
        page: int = 1,
        size: int = 10,
        current_user: JWTUser = Depends(get_current_user),
):
    tpl_svc = TplListSvc(page=page, size=size)
    data, total = await tpl_svc.list_tpl()
    return Responses.success(data={"items": data, "total": total})


@router.post(
    path="/tpls",
    summary="create",
    responses=response_docs(data={
        "id": "int",
    }),
)
async def create_tpl(
        tpl_svc: TplCreateSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    created_id = await tpl_svc.create_tpl()
    return Responses.success(data={"id": created_id})


@router.get(
    path="/tpls/{tpl_id}",
    summary="get",
    responses=response_docs(
        model=TplGetSvc,
    ),
)
async def get_tpl(
        tpl_id: int,
        current_user: JWTUser = Depends(get_current_user),  # 认证
):
    tpl_svc = TplGetSvc(tpl_id=tpl_id)
    data = await tpl_svc.get_tpl()
    return Responses.success(data=data)


@router.delete(
    path="/tpls/{tpl_id}",
    summary="delete",
    responses=response_docs(data={
        "id": "int",
    }),
)
async def delete_tpl(
        tpl_id: int,
        current_user: JWTUser = Depends(get_current_user),
):
    tpl_svc = TplDeleteSvc(tpl_id=tpl_id)
    deleted_id = await tpl_svc.delete_tpl()
    return Responses.success(data={"id": deleted_id})


@router.put(
    path="/tpls/{tpl_id}",
    summary="update",
    responses=response_docs(data={
        "id": "int",
    }),
)
async def update_tpl(
        tpl_id: int,
        tpl_svc: TplUpdateSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    updated_id = await tpl_svc.update_tpl(tpl_id)
    return Responses.success(data={"id": updated_id})
