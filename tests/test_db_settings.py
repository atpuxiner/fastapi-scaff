"""测试数据库连接配置：使用 db_config.py 中写死的连接信息。"""

from contextlib import closing

import psycopg2
import pymysql

from tests.db_config import MYSQL_TEST, POSTGRES_TEST, REDIS_TEST


def test_postgres_tests_database_is_available(postgres_test_config, sql_test_databases):
    assert postgres_test_config.database == "tests"
    with closing(
        psycopg2.connect(
            host=postgres_test_config.host,
            port=postgres_test_config.port,
            user=postgres_test_config.username,
            password=postgres_test_config.password,
            dbname=postgres_test_config.database,
            connect_timeout=3,
        )
    ) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone() == (1,)


def test_mysql_tests_database_is_available(mysql_test_config, sql_test_databases):
    assert mysql_test_config.database == "tests"
    with closing(
        pymysql.connect(
            host=mysql_test_config.host,
            port=mysql_test_config.port,
            user=mysql_test_config.username,
            password=mysql_test_config.password,
            database=mysql_test_config.database,
            connect_timeout=3,
        )
    ) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone() == (1,)


def test_redis_configured_databases_are_available(redis_test_config, redis_test_clients):
    assert redis_test_config.databases == (0, 1, 2)
    for db, client in redis_test_clients.items():
        key = f"fastapi-scaff:test:{db}"
        try:
            assert client.ping() is True
            client.set(key, "ok", ex=10)
            assert client.get(key) == "ok"
        finally:
            client.delete(key)


def test_database_env_helpers():
    assert POSTGRES_TEST.env["DB_DRIVERNAME"] == "postgresql+psycopg2"
    assert POSTGRES_TEST.env["DB_DATABASE"] == "tests"
    assert MYSQL_TEST.env["DB_DRIVERNAME"] == "mysql+pymysql"
    assert MYSQL_TEST.env["DB_CHARSET"] == "utf8mb4"
    assert REDIS_TEST.env(2)["REDIS_DB"] == "2"
    assert REDIS_TEST.env(2)["REDIS_PASSWORD"] == REDIS_TEST.password
