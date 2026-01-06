import asyncio
import importlib
import re

from sqlalchemy import URL, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept

from app import APP_DIR

_MODELS_MOD_DIR = APP_DIR.joinpath("models")
_MODELS_MOD_BASE = "app.models"
_DECL_BASE_NAME = "DeclBase"
_TABLES_CREATED = False


def init_db_session(
        db_drivername: str,
        db_database: str,
        db_username: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_charset: str,
        db_echo: bool,
        db_pool_size: int = 10,
        db_max_overflow: int = 5,
        db_pool_recycle: int = 3600,
        is_create_tables: bool = False,
) -> scoped_session:
    db_url = make_db_url(
        drivername=db_drivername,
        database=db_database,
        username=db_username,
        password=db_password,
        host=db_host,
        port=db_port,
        query={
            "charset": db_charset,
        },
    )
    db_echo = db_echo or False
    kwargs = {
        "pool_size": db_pool_size,
        "max_overflow": db_max_overflow,
        "pool_recycle": db_pool_recycle,
    }
    if db_url.drivername.startswith("sqlite"):
        kwargs = {}
    engine = create_engine(
        url=db_url,
        echo=db_echo,
        pool_pre_ping=True,
        **kwargs,
    )
    db_session = sessionmaker(engine, expire_on_commit=False)

    def create_tables():
        decl_base = import_tables()
        if decl_base:
            try:
                decl_base.metadata.create_all(engine)  # noqa
            except Exception as e:
                if "already exists" not in str(e):
                    raise

    global _TABLES_CREATED
    if is_create_tables and not _TABLES_CREATED:
        create_tables()
        _TABLES_CREATED = True

    return scoped_session(db_session)


def init_db_async_session(
        db_drivername: str,
        db_database: str,
        db_username: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_charset: str,
        db_echo: bool,
        db_pool_size: int = 10,
        db_max_overflow: int = 5,
        db_pool_recycle: int = 3600,
        is_create_tables: bool = False,
) -> sessionmaker:
    db_url = make_db_url(
        drivername=db_drivername,
        database=db_database,
        username=db_username,
        password=db_password,
        host=db_host,
        port=db_port,
        query={
            "charset": db_charset,
        },
    )
    db_echo = db_echo or False
    kwargs = {
        "pool_size": db_pool_size,
        "max_overflow": db_max_overflow,
        "pool_recycle": db_pool_recycle,
    }
    if db_url.drivername.startswith("sqlite"):
        kwargs = {}
    async_engine = create_async_engine(
        url=db_url,
        echo=db_echo,
        pool_pre_ping=True,
        **kwargs,
    )
    db_async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)  # noqa

    async def create_tables():
        decl_base = import_tables()
        if decl_base:
            async with async_engine.begin() as conn:
                try:
                    await conn.run_sync(decl_base.metadata.create_all)  # noqa
                except Exception as e:
                    if "already exists" not in str(e):
                        raise

    global _TABLES_CREATED
    if is_create_tables and not _TABLES_CREATED:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        task = loop.create_task(create_tables())
        task.add_done_callback(lambda t: t.result() if not t.cancelled() else None)
        if not loop.is_running():
            loop.run_until_complete(task)
        _TABLES_CREATED = True
    return db_async_session


def make_db_url(
        drivername: str,
        database: str,
        username: str = None,
        password: str = None,
        host: str = None,
        port: int = None,
        query: dict = None,
) -> URL:
    query = {k: v for k, v in query.items() if v} if query else {}
    return URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        query=query,
    )


def import_tables() -> DeclarativeAttributeIntercept | None:
    decl_base = getattr(importlib.import_module(_MODELS_MOD_BASE), _DECL_BASE_NAME, None)
    if isinstance(decl_base, DeclarativeAttributeIntercept):
        pat = re.compile(rf"^\s*class\s+[A-Za-z_]\w*\s*\(\s*{_DECL_BASE_NAME}\s*\)\s*:", re.MULTILINE)
        for f in _MODELS_MOD_DIR.rglob("*.py"):
            if f.name.startswith("__"):
                continue
            if pat.search(f.read_text("utf-8")):
                rel = f.relative_to(_MODELS_MOD_DIR).with_suffix("")
                _ = importlib.import_module(f"{_MODELS_MOD_BASE}.{'.'.join(rel.parts)}")
        return decl_base
