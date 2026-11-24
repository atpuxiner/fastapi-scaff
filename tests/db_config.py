"""测试环境数据库配置：连接信息集中写死在这里，避免后续重复填写。"""

from contextlib import closing
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SqlDbConfig:
    host: str
    port: int
    username: str
    password: str = field(repr=False)
    database: str = "tests"
    charset: str = ""
    drivername: str = ""
    async_drivername: str = ""

    @property
    def env(self) -> dict[str, str]:
        """返回可直接写入生成项目 config/.env 的数据库变量。"""
        return {
            "DB_DRIVERNAME": self.drivername,
            "DB_ASYNC_DRIVERNAME": self.async_drivername,
            "DB_DATABASE": self.database,
            "DB_USERNAME": self.username,
            "DB_PASSWORD": self.password,
            "DB_HOST": self.host,
            "DB_PORT": str(self.port),
            "DB_CHARSET": self.charset,
        }


@dataclass(frozen=True)
class RedisDbConfig:
    host: str
    port: int
    password: str = field(repr=False)
    databases: tuple[int, ...] = (0, 1, 2)

    def env(self, db: int = 0) -> dict[str, str]:
        """返回可直接写入生成项目 config/.env 的 Redis 变量。"""
        return {
            "REDIS_HOST": self.host,
            "REDIS_PORT": str(self.port),
            "REDIS_DB": str(db),
            "REDIS_PASSWORD": self.password,
            "REDIS_MAX_CONNECTIONS": "",
        }


POSTGRES_TEST = SqlDbConfig(
    host="127.0.0.1",
    # 需求里写的是 6379，但该端口与 Redis 冲突；实测 PostgreSQL 在 5432。
    port=5432,
    username="postgres",
    password="Mimmm@129",
    database="tests",
    drivername="postgresql+psycopg2",
    async_drivername="postgresql+asyncpg",
)

MYSQL_TEST = SqlDbConfig(
    host="127.0.0.1",
    port=3306,
    username="root",
    password="Mimmm@129",
    database="tests",
    charset="utf8mb4",
    drivername="mysql+pymysql",
    async_drivername="mysql+aiomysql",
)

REDIS_TEST = RedisDbConfig(
    host="127.0.0.1",
    port=6379,
    password="Mimmm@129",
    databases=(0, 1, 2),
)


def ensure_postgres_database(config: SqlDbConfig = POSTGRES_TEST) -> None:
    """幂等创建 PostgreSQL 测试库。"""
    import psycopg2

    with closing(
        psycopg2.connect(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            dbname="postgres",
            connect_timeout=3,
        )
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (config.database,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{config.database}"')


def ensure_mysql_database(config: SqlDbConfig = MYSQL_TEST) -> None:
    """幂等创建 MySQL 测试库。"""
    import pymysql

    with closing(
        pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            connect_timeout=3,
        )
    ) as conn:
        charset = config.charset or "utf8mb4"
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.database}` CHARACTER SET {charset}")
        conn.commit()


def reset_sql_database(config: SqlDbConfig, tables: tuple[str, ...] = ("users", "books")) -> None:
    """清空指定表，让 E2E 每次都在干净库上启动生成项目。"""
    if config.drivername.startswith("postgresql"):
        import psycopg2

        with closing(
            psycopg2.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                dbname=config.database,
                connect_timeout=3,
            )
        ) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                for table in tables:
                    cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
        return

    import pymysql

    with closing(
        pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            database=config.database,
            connect_timeout=3,
        )
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in tables:
                cur.execute(f"DROP TABLE IF EXISTS `{table}`")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()


def redis_client(db: int = 0, config: RedisDbConfig = REDIS_TEST):
    """返回指定 Redis 库的客户端。"""
    import redis

    return redis.Redis(
        host=config.host,
        port=config.port,
        db=db,
        password=config.password,
        socket_connect_timeout=3,
        decode_responses=True,
    )


def redis_clients(config: RedisDbConfig = REDIS_TEST):
    """返回配置中每个 Redis 库对应的客户端。"""
    return {db: redis_client(db, config) for db in config.databases}
