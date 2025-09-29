from app.models.user import User
from app.schemas.user import (
    UserDetail,
    UserList,
    UserCreate,
    UserUpdate,
    UserDelete,
    UserLogin,
    UserToken,
)
from app.initializer import g
from app.utils import auth_util, db_async_util


class UserDetailSvc(UserDetail):
    model_config = {
        "json_schema_extra": {
            "title": "UserDetail"
        }
    }

    async def detail(self):
        async with g.db_async_session() as session:
            data = await db_async_util.query_one(
                session=session,
                model=User,
                fields=self.response_fields(),
                filter_by={"id": self.id},
            )
            return data


class UserListSvc(UserList):
    model_config = {
        "json_schema_extra": {
            "title": "UserList"
        }
    }

    async def lst(self):
        async with g.db_async_session() as session:
            data = await db_async_util.query_all(
                session=session,
                model=User,
                fields=self.response_fields(),
                page=self.page,
                size=self.size,
            )
            total = await db_async_util.query_total(session, User)
            return data, total


class UserCreateSvc(UserCreate):
    model_config = {
        "json_schema_extra": {
            "title": "UserCreate"
        }
    }

    async def create(self):
        async with g.db_async_session() as session:
            return await db_async_util.create(
                session=session,
                model=User,
                data={
                    "name": self.name,
                    "phone": self.phone,
                    "age": self.age,
                    "gender": self.gender,
                    "password": auth_util.hash_password(self.password),
                    "jwt_key": auth_util.gen_jwt_key(),
                },
                filter_by={"phone": self.phone},
            )


class UserUpdateSvc(UserUpdate):
    model_config = {
        "json_schema_extra": {
            "title": "UserUpdate"
        }
    }

    async def update(self, user_id: str):
        async with g.db_async_session() as session:
            return await db_async_util.update(
                session=session,
                model=User,
                data=self.model_dump(),
                filter_by={"id": user_id},
            )


class UserDeleteSvc(UserDelete):
    model_config = {
        "json_schema_extra": {
            "title": "UserDelete"
        }
    }

    @staticmethod
    async def delete(user_id: str):
        async with g.db_async_session() as session:
            return await db_async_util.delete(
                session=session,
                model=User,
                filter_by={"id": user_id},
            )


class UserLoginSvc(UserLogin):
    model_config = {
        "json_schema_extra": {
            "title": "UserLogin"
        }
    }

    async def login(self):
        async with g.db_async_session() as session:
            data = await db_async_util.query_one(
                session=session,
                model=User,
                filter_by={"phone": self.phone},
            )
            if not data or not auth_util.verify_password(self.password, data.get("password")):
                return None
            new_jwt_key = auth_util.gen_jwt_key()
            token = auth_util.gen_jwt(
                payload={
                    "id": data.get("id"),
                    "phone": data.get("phone"),
                    "name": data.get("name"),
                    "age": data.get("age"),
                    "gender": data.get("gender"),
                },
                jwt_key=new_jwt_key,
                exp_minutes=24 * 60 * 30,
            )
            # 更新jwt_key
            await db_async_util.update(
                session=session,
                model=User,
                data={"jwt_key": new_jwt_key},
                filter_by={"phone": self.phone},
            )
            return token


class UserTokenSvc(UserToken):
    model_config = {
        "json_schema_extra": {
            "title": "UserToken"
        }
    }

    async def token(self):
        async with g.db_async_session() as session:
            data = await db_async_util.query_one(
                session=session,
                model=User,
                filter_by={"id": self.id},
            )
            if not data:
                return None
            new_jwt_key = auth_util.gen_jwt_key()
            token = auth_util.gen_jwt(
                payload={
                    "id": data.get("id"),
                    "phone": data.get("phone"),
                    "name": data.get("name"),
                    "age": data.get("age"),
                    "gender": data.get("gender"),
                },
                jwt_key=new_jwt_key,
                exp_minutes=self.exp_minutes,
            )
            # 更新jwt_key
            await db_async_util.update(
                session=session,
                model=User,
                data={"jwt_key": new_jwt_key},
                filter_by={"id": self.id},
            )
            return token
