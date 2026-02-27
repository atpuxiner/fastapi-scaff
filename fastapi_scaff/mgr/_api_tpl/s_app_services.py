from sqlalchemy.exc import IntegrityError

from app.api.exceptions import CustomException
from app.api.status import Status
from app.initializer import g
from app.models.tpl import Tpl


class TplSvc:

    @staticmethod
    async def list_tpl(req):
        where = []
        if req.name:
            where.append(Tpl.name.contains(req.name))
        async with g.db_async_session() as session:
            items = await Tpl.fetch_all(
                session=session,
                columns=(
                    "id",
                    "name",
                    "created_at",
                    "updated_at",
                ),
                where=where,
                order_by="-created_at",
                offset=(req.page - 1) * req.size,
                limit=req.size,
                converters={"id": str},
            )
            total = await Tpl.count(session=session, where=where)
            return {"items": items, "total": total}

    @staticmethod
    async def create_tpl(req):
        async with g.db_async_session() as session:
            result = await Tpl.create(
                session=session,
                values={
                    "name": req.name,
                },
                on_conflict={"name": req.name},
                flush=True,
            )
            if not result:
                raise CustomException(status=Status.RECORD_EXISTS_ERROR)
            await session.commit()
            return str(result.data["id"])

    @staticmethod
    async def get_tpl(tpl_id):
        async with g.db_async_session() as session:
            data = await Tpl.fetch_one(
                session=session,
                where={"id": int(tpl_id)},
                columns=(
                    "id",
                    "name",
                    "created_at",
                    "updated_at",
                ),
                converters={"id": str},
            )
            if not data:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            return data

    @staticmethod
    async def delete_tpl(tpl_id):
        async with g.db_async_session() as session:
            result = await Tpl.delete(
                session=session,
                where={"id": int(tpl_id)},
            )
            if not result:
                raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
            await session.commit()
            return tpl_id

    @staticmethod
    async def update_tpl(req, tpl_id: str):
        async with g.db_async_session() as session:
            try:
                result = await Tpl.update(
                    session=session,
                    where={"id": int(tpl_id)},
                    values=req.model_dump(),
                )
                if not result:
                    raise CustomException(status=Status.RECORD_NOT_EXIST_ERROR)
                await session.commit()
            except IntegrityError:
                raise CustomException(status=Status.RECORD_EXISTS_ERROR)
            return tpl_id
