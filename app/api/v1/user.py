from fastapi import APIRouter, Depends

from app.api.dependencies import JWTUser, get_current_user
from app.api.responses import Responses, response_docs
from app.api.status import Status
from app.services.user import (
    UserListSvc,
    UserCreateSvc,
    UserGetSvc,
    UserDeleteSvc,
    UserUpdateSvc,
    UserLoginSvc,
    UserLogoutSvc,
    UserTokenSvc,
)

router = APIRouter()
_active = True  # 激活状态（默认激活）
_tag = "user"  # 标签（默认模块名）


# 注意：`user`仅为模块示例，请根据自身需求修改
# 注意：`user`仅为模块示例，请根据自身需求修改
# 注意：`user`仅为模块示例，请根据自身需求修改


@router.get(
    path="/users",
    summary="list",
    responses=response_docs(
        model=UserListSvc,
        is_listwrap=True,
        listwrap_key="items",
        listwrap_key_extra={
            "total": "int",
        },
    ),
)
async def list_user(
        page: int = 1,
        size: int = 10,
        current_user: JWTUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        return Responses.failure(status=Status.USER_NOT_ADMIN_ERROR)
    user_svc = UserListSvc(page=page, size=size)
    data, total = await user_svc.list_user()
    return Responses.success(data={"items": data, "total": total})


@router.post(
    path="/users",
    summary="create",
    responses=response_docs(data={
        "id": "int",
    }),
)
async def create_user(
        user_svc: UserCreateSvc,
):
    created_id = await user_svc.create_user()
    return Responses.success(data={"id": created_id})


@router.get(
    path="/users/{user_id}",
    summary="get",
    responses=response_docs(
        model=UserGetSvc,
    ),
)
async def get_user(
        user_id: int,
        current_user: JWTUser = Depends(get_current_user),  # 认证
):
    user_svc = UserGetSvc(user_id=user_id)
    data = await user_svc.get_user()
    return Responses.success(data=data)


@router.delete(
    path="/users/{user_id}",
    summary="delete",
    responses=response_docs(data={
        "id": "int",
    }),
)
async def delete_user(
        user_id: int,
        current_user: JWTUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        return Responses.failure(status=Status.USER_NOT_ADMIN_ERROR)
    user_svc = UserDeleteSvc(user_id=user_id)
    deleted_id = await user_svc.delete_user()
    return Responses.success(data={"id": deleted_id})


@router.put(
    path="/users/{user_id}",
    summary="update",
    responses=response_docs(data={
        "id": "int",
    }),
)
async def update_user(
        user_id: int,
        user_svc: UserUpdateSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    updated_id = await user_svc.update_user(user_id)
    return Responses.success(data={"id": updated_id})


@router.post(
    path="/users/login",
    summary="login",
    responses=response_docs(data={
        "token": "str",
        "user": "dict"
    }),
)
async def login(
        user_svc: UserLoginSvc,
):
    data = await user_svc.login()
    return Responses.success(data=data)


@router.post(
    path="/users/logout",
    summary="logout",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def logout(
        user_svc: UserLogoutSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    data = await user_svc.logout()
    return Responses.success(data=data)


@router.post(
    path="/users/token",
    summary="token",
    responses=response_docs(data={
        "token": "str",
    }),
)
async def token(
        user_svc: UserTokenSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    data = await user_svc.token()
    return Responses.success(data={"token": data})
