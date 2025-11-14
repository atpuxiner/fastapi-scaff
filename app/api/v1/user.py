from fastapi import APIRouter, Depends

from app.api.dependencies import JWTUser, get_current_user
from app.api.responses import Responses, response_docs
from app.api.status import Status
from app.initializer import g
from app.services.user import (
    UserDetailSvc,
    UserListSvc,
    UserCreateSvc,
    UserUpdateSvc,
    UserDeleteSvc,
    UserLoginSvc,
    UserTokenSvc,
)

router = APIRouter()
_active = True  # 激活状态（默认激活）
_tag = "user"  # 标签（默认模块名）


# 注意：`user`仅为模块示例，请根据自身需求修改
# 注意：`user`仅为模块示例，请根据自身需求修改
# 注意：`user`仅为模块示例，请根据自身需求修改


@router.get(
    path="/user/{user_id}",
    summary="userDetail",
    responses=response_docs(
        model=UserDetailSvc,
    ),
)
async def detail(
        user_id: str,
        current_user: JWTUser = Depends(get_current_user),  # 认证
):
    try:
        user_svc = UserDetailSvc(id=user_id)
        data = await user_svc.detail()
        if not data:
            return Responses.failure(status=Status.RECORD_NOT_EXIST_ERROR)
    except Exception as e:
        msg = "userDetail操作异常"
        g.logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data=data)


@router.get(
    path="/user",
    summary="userList",
    responses=response_docs(
        model=UserListSvc,
        is_listwrap=True,
        listwrap_key="items",
        listwrap_key_extra={
            "total": "int",
        },
    ),
)
async def lst(
        page: int = 1,
        size: int = 10,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        user_svc = UserListSvc(page=page, size=size)
        data, total = await user_svc.lst()
    except Exception as e:
        msg = "userList操作异常"
        g.logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data={"items": data, "total": total})


@router.post(
    path="/user",
    summary="userCreate",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def create(
        user_svc: UserCreateSvc,
):
    try:
        user_id = await user_svc.create()
        if not user_id:
            return Responses.failure(status=Status.RECORD_EXISTS_ERROR)
    except Exception as e:
        msg = "userCreate操作异常"
        g.logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data={"id": user_id})


@router.put(
    path="/user/{user_id}",
    summary="userUpdate",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def update(
        user_id: str,
        user_svc: UserUpdateSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        updated_ids = await user_svc.update(user_id)
        if not updated_ids:
            return Responses.failure(status=Status.RECORD_NOT_EXIST_ERROR)
    except Exception as e:
        msg = "userUpdate操作异常"
        g.logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data={"id": user_id})


@router.delete(
    path="/user/{user_id}",
    summary="userDelete",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def delete(
        user_id: str,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        user_svc = UserDeleteSvc()
        deleted_ids = await user_svc.delete(user_id)
        if not deleted_ids:
            return Responses.failure(status=Status.RECORD_NOT_EXIST_ERROR)
    except Exception as e:
        msg = "userDelete操作异常"
        g.logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data={"id": user_id})


@router.post(
    path="/user/login",
    summary="userLogin",
    responses=response_docs(data={
        "token": "str",
    }),
)
async def login(
        user_svc: UserLoginSvc,
):
    try:
        data = await user_svc.login()
        if not data:
            return Responses.failure(status=Status.USER_OR_PASSWORD_ERROR)
    except Exception as e:
        msg = "userLogin操作异常"
        g.logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data={"token": data})


@router.post(
    path="/user/token",
    summary="userToken",
    responses=response_docs(data={
        "token": "str",
    }),
)
async def token(
        user_svc: UserTokenSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        data = await user_svc.token()
        if not data:
            return Responses.failure(status=Status.RECORD_NOT_EXIST_ERROR)
    except Exception as e:
        msg = "userToken操作异常"
        g.logger.exception(msg)
        return Responses.failure(msg=msg, error=e)
    return Responses.success(data={"token": data})
