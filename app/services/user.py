from app.api.exceptions import CustomException
from app.api.status import Status
from app.initializer import g
from app.repositories.user import UserRepo
from app.schemas.user import (
    UserDetail,
    UserList,
    UserCreate,
    UserUpdate,
    UserDelete,
    UserLogin,
    UserToken,
)
from app.utils import jwt_util


class UserDetailSvc(UserDetail):
    model_config = {
        "json_schema_extra": {
            "title": "UserDetail"
        }
    }

    async def detail(self):
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            data = await user_repo.get_user_detail(
                fields=self.response_fields(),
                filter_by={"id": self.id},
            )
            if not data:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            return data


class UserListSvc(UserList):
    model_config = {
        "json_schema_extra": {
            "title": "UserList"
        }
    }

    async def lst(self):
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            data = await user_repo.get_user_lst(
                fields=self.response_fields(),
                page=self.page,
                size=self.size,
            )
            total = await user_repo.get_user_total()
            return data, total


class UserCreateSvc(UserCreate):
    model_config = {
        "json_schema_extra": {
            "title": "UserCreate"
        }
    }

    async def create(self):
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            user = await user_repo.create_user(
                data={
                    "name": self.name,
                    "phone": self.phone,
                    "age": self.age,
                    "gender": self.gender,
                    "password": jwt_util.hash_password(self.password),
                    "jwt_key": jwt_util.gen_jwt_key(),
                },
                check_unique={"phone": self.phone},
            )
            if not user:
                raise CustomException(status=Status.RECORD_EXISTS_ERROR)
            await session.commit()
            return user.id


class UserUpdateSvc(UserUpdate):
    model_config = {
        "json_schema_extra": {
            "title": "UserUpdate"
        }
    }

    async def update(self, user_id: str):
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            rowcount = await user_repo.update_user(
                data=self.model_dump(),
                filter_by={"id": user_id},
            )
            if not rowcount:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
            return user_id


class UserDeleteSvc(UserDelete):
    model_config = {
        "json_schema_extra": {
            "title": "UserDelete"
        }
    }

    @staticmethod
    async def delete(user_id: str):
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            rowcount = await user_repo.delete_user(
                filter_by={"id": user_id},
            )
            if not rowcount:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
            return user_id


class UserLoginSvc(UserLogin):
    model_config = {
        "json_schema_extra": {
            "title": "UserLogin"
        }
    }

    async def login(self):
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            data = await user_repo.get_user_detail(
                fields=("id", "phone", "name", "age", "gender", "password"),
                filter_by={"phone": self.phone},
            )
            if not data:
                raise CustomException(status=Status.USER_OR_PASSWORD_ERROR)
            stored_password = data["password"]
            payload = {
                "id": data.get("id"),
                "phone": data.get("phone"),
                "name": data.get("name"),
                "age": data.get("age"),
                "gender": data.get("gender"),
            }

        if not jwt_util.verify_password(self.password, stored_password):
            raise CustomException(status=Status.USER_OR_PASSWORD_ERROR)
        new_jwt_key = jwt_util.gen_jwt_key()
        token = jwt_util.gen_jwt(
            payload=payload,
            jwt_key=new_jwt_key,
            exp_minutes=24 * 60 * 30,
        )
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            await user_repo.update_user(
                data={"jwt_key": new_jwt_key},
                filter_by={"phone": self.phone},
            )
            await session.commit()

        return token


class UserTokenSvc(UserToken):
    model_config = {
        "json_schema_extra": {
            "title": "UserToken"
        }
    }

    async def token(self):
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            data = await user_repo.get_user_detail(
                fields=("id", "phone", "name", "age", "gender"),
                filter_by={"id": self.id},
            )
            if not data:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            payload = {
                "id": data.get("id"),
                "phone": data.get("phone"),
                "name": data.get("name"),
                "age": data.get("age"),
                "gender": data.get("gender"),
            }

        new_jwt_key = jwt_util.gen_jwt_key()
        token = jwt_util.gen_jwt(
            payload=payload,
            jwt_key=new_jwt_key,
            exp_minutes=self.exp_minutes,
        )
        async with g.db_async_session() as session:
            user_repo = UserRepo(session)
            await user_repo.update_user(
                data={"jwt_key": new_jwt_key},
                filter_by={"id": self.id},
            )
            await session.commit()

        return token
