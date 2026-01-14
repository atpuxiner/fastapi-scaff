from sqlalchemy import (
    select,
    func,
    text,
    update as update_,
    delete as delete_,
)
from sqlalchemy.ext.asyncio import AsyncSession


def format_all(
        rows,
        fields: list[str] | tuple[str],
) -> list[dict]:
    if not rows:
        return []
    return [dict(zip(fields, row)) for row in rows]


def format_one(
        row,
        fields: list[str] | tuple[str],
) -> dict:
    if not row:
        return {}
    return dict(zip(fields, row))


def model_dict(
        model,
        fields: list[str] | tuple[str] | None = None,
) -> dict:
    if not model:
        return {}
    if fields is None:
        fields = [field.name for field in model.__table__.columns]
    return {field: getattr(model, field) for field in fields}


async def fetch_one(
        session: AsyncSession,
        model,
        *,
        fields: list[str] | tuple[str] | None = None,
        filter_by: dict | None = None,
) -> dict:
    if fields is None:
        fields = [field.name for field in model.__table__.columns]
    cols = [getattr(model, field) for field in fields if hasattr(model, field)]
    query = select(*cols).select_from(model)
    if filter_by:
        query = query.filter_by(**filter_by)
    result = await session.execute(query)
    return format_one(result.fetchone(), fields)


async def fetch_all(
        session: AsyncSession,
        model,
        *,
        fields: list[str] | tuple[str] | None = None,
        filter_by: dict | None = None,
        page: int | None = None,
        size: int | None = None,
) -> list[dict]:
    if fields is None:
        fields = [field.name for field in model.__table__.columns]
    cols = [getattr(model, field) for field in fields if hasattr(model, field)]
    query = select(*cols).select_from(model)
    if filter_by:
        query = query.filter_by(**filter_by)
    if page is not None and size is not None:
        query = query.offset((page - 1) * size).limit(size)
    result = await session.execute(query)
    return format_all(result.fetchall(), fields)


async def fetch_total(
        session: AsyncSession,
        model,
        *,
        filter_by: dict | None = None,
) -> int:
    query = select(func.count()).select_from(model)
    if filter_by:
        query = query.filter_by(**filter_by)
    result = await session.execute(query)
    return result.scalar() or 0


async def create(
        session: AsyncSession,
        model,
        *,
        data: dict,
        check_unique: dict | None = None,
        flush: bool = False,
) -> object | None:
    if check_unique:
        exists = await fetch_one(session, model, filter_by=check_unique)
        if exists:
            return None
    obj = model(**data)
    session.add(obj)
    if flush:
        await session.flush()
    return obj


async def update(
        session: AsyncSession,
        model,
        *,
        data: dict,
        filter_by: dict,
        is_exclude_none: bool = True,
) -> int:
    if not filter_by:
        raise ValueError("update requires non-empty filter_by to avoid full-table update")
    if is_exclude_none:
        data = {k: v for k, v in data.items() if v is not None}
    stmt = update_(model).filter_by(**filter_by).values(**data)
    result = await session.execute(stmt)
    return result.rowcount  # noqa


async def delete(
        session: AsyncSession,
        model,
        *,
        filter_by: dict,
) -> int:
    if not filter_by:
        raise ValueError("delete requires non-empty filter_by to avoid full-table delete")
    stmt = delete_(model).filter_by(**filter_by)
    result = await session.execute(stmt)
    return result.rowcount  # noqa


async def sqlfetch_one(
        session: AsyncSession,
        sql: str,
        *,
        params: dict | None = None,
) -> dict:
    result = await session.execute(text(sql), params)
    row = result.fetchone()
    return row._asdict() if row else {}  # noqa


async def sqlfetch_all(
        session: AsyncSession,
        sql: str,
        *,
        params: dict | None = None,
) -> list[dict]:
    result = await session.execute(text(sql), params)
    rows = result.fetchall()
    return [row._asdict() for row in rows]  # noqa
