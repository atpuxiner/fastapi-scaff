import traceback

from fastapi import APIRouter, Depends
from starlette.requests import Request

from app.api.response import Response, response_docs
from app.api.status import Status
from app.service.user import (
    UserDetailSvc,
    UserListSvc,
    UserCreateSvc,
    UserUpdateSvc,
    UserDeleteSvc,
    UserLoginSvc,
    UserTokenSvc,
)
from app.initializer import g
from app.middleware.auth import JWTUser, get_current_user

user_router = APIRouter()
_active = True  # 激活状态（默认激活）
_tag = "user"  # 标签（默认模块名或子目录名）


# 注意：`user`仅为模块示例，请根据自身需求修改
# 注意：`user`仅为模块示例，请根据自身需求修改
# 注意：`user`仅为模块示例，请根据自身需求修改


@user_router.get(
    path="/user/{user_id}",
    summary="userDetail",
    responses=response_docs(
        model=UserDetailSvc,
    ),
)
async def detail(
        request: Request,
        user_id: str,
        current_user: JWTUser = Depends(get_current_user),  # 认证
):
    try:
        user_svc = UserDetailSvc(id=user_id)
        data = await user_svc.detail()
        if not data:
            return Response.failure(status=Status.RECORD_NOT_EXIST_ERROR)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="userDetail失败", error=e, request=request)
    return Response.success(data=data, request=request)


@user_router.get(
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
        request: Request,
        page: int = 1,
        size: int = 10,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        user_svc = UserListSvc(page=page, size=size)
        data, total = await user_svc.lst()
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="userList失败", error=e, request=request)
    return Response.success(data={"items": data, "total": total}, request=request)


@user_router.post(
    path="/user",
    summary="userCreate",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def create(
        request: Request,
        user_svc: UserCreateSvc,
):
    try:
        user_id = await user_svc.create()
        if not user_id:
            return Response.failure(status=Status.RECORD_EXISTS_ERROR, request=request)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="userCreate失败", error=e, request=request)
    return Response.success(data={"id": user_id}, request=request)


@user_router.put(
    path="/user/{user_id}",
    summary="userUpdate",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def update(
        request: Request,
        user_id: str,
        user_svc: UserUpdateSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        updated_ids = await user_svc.update(user_id)
        if not updated_ids:
            return Response.failure(status=Status.RECORD_NOT_EXIST_ERROR, request=request)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="userUpdate失败", error=e, request=request)
    return Response.success(data={"id": user_id}, request=request)


@user_router.delete(
    path="/user/{user_id}",
    summary="userDelete",
    responses=response_docs(data={
        "id": "str",
    }),
)
async def delete(
        request: Request,
        user_id: str,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        user_svc = UserDeleteSvc()
        deleted_ids = await user_svc.delete(user_id)
        if not deleted_ids:
            return Response.failure(status=Status.RECORD_NOT_EXIST_ERROR, request=request)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="userDelete失败", error=e, request=request)
    return Response.success(data={"id": user_id}, request=request)


@user_router.post(
    path="/user/login",
    summary="userLogin",
    responses=response_docs(data={
        "token": "str",
    }),
)
async def login(
        request: Request,
        user_svc: UserLoginSvc,
):
    try:
        data = await user_svc.login()
        if not data:
            return Response.failure(status=Status.USER_OR_PASSWORD_ERROR, request=request)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="userLogin失败", error=e, request=request)
    return Response.success(data={"token": data}, request=request)


@user_router.post(
    path="/user/token",
    summary="userToken",
    responses=response_docs(data={
        "token": "str",
    }),
)
async def token(
        request: Request,
        user_svc: UserTokenSvc,
        current_user: JWTUser = Depends(get_current_user),
):
    try:
        data = await user_svc.token()
        if not data:
            return Response.failure(status=Status.RECORD_NOT_EXIST_ERROR, request=request)
    except Exception as e:
        g.logger.error(traceback.format_exc())
        return Response.failure(msg="userToken失败", error=e, request=request)
    return Response.success(data={"token": data}, request=request)
