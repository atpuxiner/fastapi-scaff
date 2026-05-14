import importlib
import re

from sqlalchemy import URL, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept

from app import APP_DIR

_MODELS_MOD_DIR = APP_DIR.joinpath("models")
_MODELS_MOD_BASE = "app.models"
_DECL_BASE_NAME = "DeclBase"


def init_db_async_session(
    db_async_drivername: str,
    db_database: str,
    db_username: str,
    db_password: str,
    db_host: str,
    db_port: int,
    db_charset: str | None = None,
    db_echo: bool | None = None,
    db_pool_size: int = 10,
    db_max_overflow: int = 5,
    db_pool_recycle: int = 3600,
    db_drivername: str | None = None,
) -> async_sessionmaker[AsyncSession]:
    db_url = make_db_url(
        drivername=db_async_drivername,
        database=db_database,
        username=db_username,
        password=db_password,
        host=db_host,
        port=db_port,
        query={"charset": db_charset},
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
    db_async_session = async_sessionmaker[AsyncSession](async_engine, expire_on_commit=False)
    if db_drivername:
        create_tables(
            db_drivername=db_drivername,
            db_database=db_database,
            db_username=db_username,
            db_password=db_password,
            db_host=db_host,
            db_port=db_port,
            db_charset=db_charset,
            db_echo=db_echo,
        )
    return db_async_session


def make_db_url(
    drivername: str,
    database: str,
    username: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: int | None = None,
    query: dict | None = None,
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
    if not _MODELS_MOD_DIR:
        return None
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


def create_tables(
    db_drivername: str,
    db_database: str,
    db_username: str,
    db_password: str,
    db_host: str,
    db_port: int,
    db_charset: str | None = None,
    db_echo: bool | None = None,
):
    sync_url = make_db_url(
        drivername=db_drivername,
        database=db_database,
        username=db_username,
        password=db_password,
        host=db_host,
        port=db_port,
        query={"charset": db_charset},
    )
    engine = create_engine(url=sync_url, echo=db_echo)
    decl_base = import_tables()
    if decl_base:
        try:
            decl_base.metadata.create_all(engine)  # type: ignore
        except Exception as e:
            if "already exists" not in str(e):
                raise
    engine.dispose()
