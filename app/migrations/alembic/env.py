from logging.config import fileConfig
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from app.initializer import g
from app.initializer._db import import_tables, make_db_url  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
decl_base = import_tables()
if not decl_base:
    raise RuntimeError("Failed to import DeclBase. Make sure your models are correctly defined and accessible.")
target_metadata = decl_base.metadata  # noqa

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
db_url = make_db_url(
    drivername=g.config.db_drivername,
    database=g.config.db_database,
    username=g.config.db_username,
    password=g.config.db_password,
    host=g.config.db_host,
    port=g.config.db_port,
    query={
        "charset": g.config.db_charset,
    },
)
db_password = quote_plus(db_url.password).replace("%", "%%") if db_url.password else ""
db_url_str = str(db_url).replace("***", db_password)
config.set_main_option(
    name="sqlalchemy.url",
    value=db_url_str,
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
