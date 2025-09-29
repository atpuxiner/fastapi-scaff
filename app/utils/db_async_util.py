from sqlalchemy import (
    select,
    func,
    update as update_,
    delete as delete_,
)


def format_all(
        rows,
        fields: list[str],
) -> list[dict]:
    if not rows:
        return list()
    return [dict(zip(fields, row)) for row in rows]


def format_one(
        row,
        fields: list[str],
) -> dict:
    if not row:
        return {}
    return dict(zip(fields, row))


def model_dict(
        model,
        fields: list[str] = None,
) -> dict:
    if not model:
        return {}
    if not fields:
        fields = [field.name for field in model.__table__.columns]
    return {field: getattr(model, field) for field in fields}


async def query_one(
        session,
        model,
        fields: list[str] = None,
        filter_by: dict = None,
) -> dict:
    if not fields:
        fields = [field.name for field in model.__table__.columns]
    query = select(*[getattr(model, field) for field in fields if hasattr(model, field)]).select_from(model)
    if filter_by:
        query = query.filter_by(**filter_by)
    result = await session.execute(query)
    return format_one(result.fetchone(), fields)


async def query_all(
        session,
        model,
        fields: list[str] = None,
        filter_by: dict = None,
        page: int = None,
        size: int = None,
) -> list[dict]:
    if not fields:
        fields = [field.name for field in model.__table__.columns]
    query = select(*[getattr(model, field) for field in fields if hasattr(model, field)]).select_from(model)
    if filter_by:
        query = query.filter_by(**filter_by)
    if page and size:
        query = query.offset((page - 1) * size).limit(size)
    result = await session.execute(query)
    return format_all(result.fetchall(), fields)


async def query_total(
        session,
        model,
        filter_by: dict = None,
) -> int:
    query = select(func.count()).select_from(model)
    if filter_by:
        query = query.filter_by(**filter_by)
    result = await session.execute(query)
    return result.scalar()


async def create(
        session,
        model,
        data: dict,
        filter_by: dict = None,
) -> int:
    try:
        if filter_by:
            result = await query_one(session, model, filter_by=filter_by)
            if result:
                return 0
        stmt = model(**data)
        session.add(stmt)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return stmt.id


async def update(
        session,
        model,
        data: dict,
        filter_by: dict | None,
        is_exclude_none: bool = True,
) -> list:
    try:
        if is_exclude_none:
            data = {k: v for k, v in data.items() if v is not None}
        stmt = update_(model).values(**data)
        if filter_by:
            stmt = stmt.filter_by(**filter_by)
        if session.bind.dialect.name == "postgresql":
            stmt = stmt.returning(model.id)
            result = await session.execute(stmt)
            updated_ids = [row[0] for row in result]
        else:
            query_stmt = select(model.id).filter_by(**filter_by)
            result = await session.execute(query_stmt)
            updated_ids = result.scalars().all()
            if updated_ids:
                await session.execute(stmt)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return updated_ids


async def delete(
        session,
        model,
        filter_by: dict | None,
) -> list:
    try:
        stmt = delete_(model)
        if filter_by:
            stmt = stmt.filter_by(**filter_by)
        if session.bind.dialect.name == "postgresql":
            stmt = stmt.returning(model.id)
            result = await session.execute(stmt)
            deleted_ids = [row[0] for row in result]
        else:
            query_stmt = select(model.id).filter_by(**filter_by)
            result = await session.execute(query_stmt)
            deleted_ids = result.scalars().all()
            if deleted_ids:
                await session.execute(stmt)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return deleted_ids
