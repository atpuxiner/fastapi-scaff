from fastapi import APIRouter, Depends

from app.api.dependencies import JWTUser, get_current_user, get_current_user_from_refresh_token
from app.api.responses import Responses, response_docs
from app.api.status import Status
from app.initializer import g
from app.models.user import (
    UserList,
    UserCreate,
    UserUpdate,
    UserLogin,
)
from app.services.user import UserSvc
from app.utils.cookie_util import set_refresh_token_cookie, clear_refresh_token_cookie

router = APIRouter()
_active = True  # 激活状态（默认激活）
_tag = "user"  # 标签（默认模块名）

# 注意：`user`仅为模块示例，请根据自身需求修改
# 注意：`user`仅为模块示例，请根据自身需求修改
# 注意：`user`仅为模块示例，请根据自身需求修改

user_svc = UserSvc()


@router.get(
    path="/users",
    summary="list",
    responses=response_docs(data={
        "items": [{
            "id": "str",
            "phone": "str",
            "status": "int",
            "role": "str",
            "name": "str",
            "age": "int",
            "gender": "int",
            "created_at": "int",
            "updated_at": "int",
        }],
        "total": "int",
    }),
)
async def list_user(
    page: int = 1,
    size: int = 10,
    current_user: JWTUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        return Responses.failure(status=Status.USER_NOT_ADMIN_ERROR)
    req = UserList(
        page=page,
        size=size,
    )
    data = await user_svc.list_user(req)
    return Responses.success(data=data)


@router.post(
    path="/users",
    summary="create",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def create_user(
    req: UserCreate,
):
    created_id = await user_svc.create_user(req)
    return Responses.success(data={"id": created_id})


@router.get(
    path="/users/{user_id}",
    summary="get",
    responses=response_docs(data={
        "id": "str",
        "phone": "str",
        "status": "int",
        "role": "str",
        "name": "str",
        "age": "int",
        "gender": "int",
        "created_at": "int",
        "updated_at": "int",
    }),
)
async def get_user(
    user_id: str,
    current_user: JWTUser = Depends(get_current_user),  # 认证
):
    data = await user_svc.get_user(user_id)
    return Responses.success(data=data)


@router.delete(
    path="/users/{user_id}",
    summary="delete",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def delete_user(
    user_id: str,
    current_user: JWTUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        return Responses.failure(status=Status.USER_NOT_ADMIN_ERROR)
    deleted_id = await user_svc.delete_user(user_id)
    return Responses.success(data={"id": deleted_id})


@router.put(
    path="/users/{user_id}",
    summary="update",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def update_user(
    user_id: str,
    req: UserUpdate,
    current_user: JWTUser = Depends(get_current_user),
):
    updated_id = await user_svc.update_user(req, user_id=user_id)
    return Responses.success(data={"id": updated_id})


@router.post(
    path="/users/login",
    summary="login",
    responses=response_docs(data={
        "access_token": "str",
        "token_type": "str",
        "expires_in": "int",
        "user_info": {
            "id": "str",
            "phone": "str",
            "status": "int",
            "role": "str",
            "name": "str",
            "age": "int",
            "gender": "int",
        }
    }),
)
async def login_user(
    req: UserLogin,
):
    data = await user_svc.login_user(req)
    refresh_token = data.pop("refresh_token")
    refresh_expires_in = data.pop("refresh_expires_in")
    response = Responses.success(data=data)
    set_refresh_token_cookie(
        response,
        refresh_token=refresh_token,
        max_age=refresh_expires_in,
        secure=(g.config.app_env == "prod"),
    )
    return response


@router.post(
    path="/users/logout",
    summary="logout",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def logout_user(
    current_user: JWTUser = Depends(get_current_user),
):
    data = await user_svc.logout_user(current_user.id)
    response = Responses.success(data=data)
    clear_refresh_token_cookie(response)
    return response


@router.post(
    path="/users/refresh-token",
    summary="refresh-token",
    responses=response_docs(data={
        "access_token": "str",
        "token_type": "str",
        "expires_in": "int",
    }),
)
async def refresh_token_user(
    current_user: JWTUser = Depends(get_current_user_from_refresh_token),
):
    data = await user_svc.refresh_token_user(current_user.id)
    refresh_token = data.pop("refresh_token")
    refresh_expires_in = data.pop("refresh_expires_in")
    response = Responses.success(data=data)
    set_refresh_token_cookie(
        response,
        refresh_token=refresh_token,
        max_age=refresh_expires_in,
        secure=(g.config.app_env == "prod"),
    )
    return response
