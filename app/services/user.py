from app.api.exceptions import CustomException
from app.api.status import Status
from app.initializer import g
from app.models.user import User
from app.utils import jwt_util

_ACCESS_TOKEN_EXP_SECONDS = 30 * 60
_REFRESH_TOKEN_EXP_SECONDS = 30 * 24 * 60 * 60


class UserSvc:

    @staticmethod
    async def list_user(req):
        async with g.db_async_session() as session:
            items = await User.fetch_all(
                session=session,
                columns=(
                    "id",
                    "phone",
                    "status",
                    "role",
                    "name",
                    "age",
                    "gender",
                    "created_at",
                    "updated_at",
                ),
                order_by="-created_at",
                offset=(req.page - 1) * req.size,
                limit=req.size,
                converters={"id": str},
            )
            total = await User.count(session=session)
            return {"items": items, "total": total}

    @staticmethod
    async def create_user(req):
        async with g.db_async_session() as session:
            result = await User.create(
                session=session,
                values={
                    "phone": req.phone,
                    "password": jwt_util.hash_password(req.password),
                    "jwt_key": jwt_util.gen_jwt_key(jwt_key=g.config.jwt_key),
                    "role": req.role,
                    "name": req.name,
                    "age": req.age,
                    "gender": req.gender,
                },
                on_conflict={"phone": req.phone},
                flush=True,
            )
            if not result:
                raise CustomException(status=Status.RECORD_EXISTS_ERROR)
            await session.commit()
            return str(result.data["id"])

    @staticmethod
    async def get_user(user_id: str):
        async with g.db_async_session() as session:
            data = await User.fetch_one(
                session=session,
                where={"id": int(user_id)},
                columns=(
                    "id",
                    "phone",
                    "status",
                    "role",
                    "name",
                    "age",
                    "gender",
                    "created_at",
                    "updated_at",
                ),
                converters={"id": str},
            )
            if not data:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            return data

    @staticmethod
    async def delete_user(user_id):
        async with g.db_async_session() as session:
            result = await User.delete(
                session=session,
                where={"id": int(user_id)},
            )
            if not result:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
            return user_id

    @staticmethod
    async def update_user(req, user_id: str):
        async with g.db_async_session() as session:
            result = await User.update(
                session=session,
                where={"id": int(user_id)},
                values=req.model_dump(),
            )
            if not result:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
            return user_id

    @staticmethod
    async def login_user(req):
        async with g.db_async_session() as session:
            data = await User.fetch_one(
                session=session,
                where={"phone": req.phone},
                columns=(
                    "id",
                    "phone",
                    "status",
                    "role",
                    "name",
                    "age",
                    "gender",
                    "password",
                ),
                converters={"id": str},
            )
            if not data:
                raise CustomException(status=Status.USER_OR_PASSWORD_ERROR)
            if data.get("status", 1) != 1:
                raise CustomException(status=Status.USER_ABNORMAL_ERROR)
            stored_password = data.pop("password")

        if not jwt_util.verify_password(req.password, stored_password):
            raise CustomException(status=Status.USER_OR_PASSWORD_ERROR)

        new_jwt_key = jwt_util.gen_jwt_key(jwt_key=g.config.jwt_key)
        access_token = jwt_util.gen_jwt(
            payload=data,
            jwt_key=new_jwt_key,
            token_type="access",
            exp_seconds=_ACCESS_TOKEN_EXP_SECONDS,
        )
        refresh_token = jwt_util.gen_jwt(
            payload={"id": data.get("id")},
            jwt_key=new_jwt_key,
            token_type="refresh",
            exp_seconds=_REFRESH_TOKEN_EXP_SECONDS,
        )
        async with g.db_async_session() as session:
            await User.update(
                session=session,
                where={"phone": req.phone},
                values={"jwt_key": new_jwt_key},
            )
            await session.commit()

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": _ACCESS_TOKEN_EXP_SECONDS,
            "user_info": data,
            "refresh_token": refresh_token,
            "refresh_expires_in": _REFRESH_TOKEN_EXP_SECONDS,
        }

    @staticmethod
    async def logout_user(user_id: str):
        new_jwt_key = jwt_util.gen_jwt_key(jwt_key=g.config.jwt_key)
        async with g.db_async_session() as session:
            result = await User.update(
                session=session,
                where={"id": int(user_id)},
                values={"jwt_key": new_jwt_key},
            )
            if not result:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
        return {"id": user_id}

    @staticmethod
    async def refresh_token_user(user_id: str):
        async with g.db_async_session() as session:
            data = await User.fetch_one(
                session=session,
                where={"id": int(user_id)},
                columns=(
                    "id",
                    "phone",
                    "status",
                    "role",
                    "name",
                    "age",
                    "gender",
                ),
                converters={"id": str},
            )
            if not data:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            if data.get("status", 1) != 1:
                raise CustomException(status=Status.USER_ABNORMAL_ERROR)

        new_jwt_key = jwt_util.gen_jwt_key(jwt_key=g.config.jwt_key)
        access_token = jwt_util.gen_jwt(
            payload=data,
            jwt_key=new_jwt_key,
            token_type="access",
            exp_seconds=_ACCESS_TOKEN_EXP_SECONDS,
        )
        refresh_token = jwt_util.gen_jwt(
            payload={"id": data.get("id")},
            jwt_key=new_jwt_key,
            token_type="refresh",
            exp_seconds=_REFRESH_TOKEN_EXP_SECONDS,
        )
        async with g.db_async_session() as session:
            await User.update(
                session=session,
                where={"id": int(user_id)},
                values={"jwt_key": new_jwt_key},
            )
            await session.commit()

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": _ACCESS_TOKEN_EXP_SECONDS,
            "refresh_token": refresh_token,
            "refresh_expires_in": _REFRESH_TOKEN_EXP_SECONDS,
        }
