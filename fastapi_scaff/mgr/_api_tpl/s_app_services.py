from pydantic import Field, BaseModel
from sqlalchemy.exc import IntegrityError

from app.api.exceptions import CustomException
from app.api.status import Status
from app.initializer import g
from app.models.tpl import Tpl


class TplListSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "TplList"
        }
    }
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=200)

    async def list_tpl(self):
        async with g.db_async_session() as session:
            data = await Tpl.fetch_all(
                session=session,
                columns=self.response_fields(),
                offset=(self.page - 1) * self.size,
                limit=self.size,
            )
            total = await Tpl.count(session=session)
            return data, total

    @staticmethod
    def response_fields():
        return (
            "id",
            "name",
            "created_at",
            "updated_at",
        )


class TplCreateSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "TplCreate"
        }
    }
    name: str | None = Field(min_length=1, max_length=50)

    async def create_tpl(self):
        async with g.db_async_session() as session:
            result = await Tpl.create(
                session=session,
                values={
                    "name": self.name,
                },
                on_conflict={"name": self.name},
                flush=True,
            )
            if not result:
                raise CustomException(status=Status.RECORD_EXISTS_ERROR)
            await session.commit()
            return result.data["id"]


class TplGetSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "TplGet"
        }
    }
    tpl_id: int = Field(...)

    async def get_tpl(self):
        async with g.db_async_session() as session:
            data = await Tpl.fetch_one(
                session=session,
                where={"id": self.tpl_id},
                columns=self.response_fields(),
            )
            if not data:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            return data

    @staticmethod
    def response_fields():
        return (
            "id",
            "name",
            "created_at",
            "updated_at",
        )


class TplDeleteSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "TplDelete"
        }
    }
    tpl_id: int = Field(...)

    async def delete_tpl(self):
        async with g.db_async_session() as session:
            result = await Tpl.delete(
                session=session,
                where={"id": self.tpl_id},
            )
            if not result:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
            return self.tpl_id


class TplUpdateSvc(BaseModel):
    model_config = {
        "json_schema_extra": {
            "title": "TplUpdate"
        }
    }
    name: str | None = Field(None)

    async def update_tpl(self, tpl_id: int):
        async with g.db_async_session() as session:
            try:
                result = await Tpl.update(
                    session=session,
                    where={"id": tpl_id},
                    values=self.model_dump(),
                )
                if not result:
                    raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
                await session.commit()
            except IntegrityError:
                raise CustomException(status=Status.RECORD_EXISTS_ERROR)
            return tpl_id
