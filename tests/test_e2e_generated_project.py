"""端到端测试：生成项目 -> add API -> 真实启动服务 -> 调用生成后的接口。"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from tests.db_config import (
    MYSQL_TEST,
    POSTGRES_TEST,
    REDIS_TEST,
    redis_client,
    reset_sql_database,
)

_ADMIN_PHONE = "13800000001"
_ADMIN_PASSWORD = "Admin123456!"
_USER_PHONE = "13800000002"
_USER_PASSWORD = "Test123456!"
_SNOW_WORKER_ID_KEY = "config:snow_worker_id_incr"
_SNOW_DATACENTER_ID_KEY = "config:snow_datacenter_id_incr"
_OPTIONAL_FLAGS = ("--loguru", "--redis", "--snow", "--migration", "--celery", "--docker")
_SQL_CONFIGS = {"mysql": MYSQL_TEST, "postgresql": POSTGRES_TEST}


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_health(client: httpx.Client, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            if client.get("/health").status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(0.2)
    raise AssertionError(f"generated server did not become healthy: {last_error}")


def _assert_ok(response: httpx.Response) -> dict:
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["code"] == 0, body
    return body["data"]


def _stop_server(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _exercise_api(client: httpx.Client) -> None:
    admin = _assert_ok(
        client.post(
            "/api/v1/users",
            json={
                "phone": _ADMIN_PHONE,
                "password": _ADMIN_PASSWORD,
                "role": "admin",
                "nickname": "e2e-admin",
            },
        )
    )
    assert admin["id"]

    login = _assert_ok(
        client.post(
            "/api/v1/users/auth/login",
            json={"phone": _ADMIN_PHONE, "password": _ADMIN_PASSWORD},
        )
    )
    assert login["access_token"] and login["user_info"]["role"] == "admin"
    client.headers.update({"Authorization": f"Bearer {login['access_token']}"})

    user = _assert_ok(
        client.post(
            "/api/v1/users",
            json={"phone": _USER_PHONE, "password": _USER_PASSWORD, "nickname": "e2e-user"},
        )
    )
    user_id = user["id"]

    listed = _assert_ok(client.get("/api/v1/users", params={"page": 1, "size": 10}))
    assert any(item["id"] == user_id for item in listed["items"])
    assert _assert_ok(client.get(f"/api/v1/users/{user_id}"))["phone"] == _USER_PHONE

    _assert_ok(client.put(f"/api/v1/users/{user_id}", json={"nickname": "e2e-updated"}))
    assert _assert_ok(client.get(f"/api/v1/users/{user_id}"))["nickname"] == "e2e-updated"
    _assert_ok(client.delete(f"/api/v1/users/{user_id}"))

    book = _assert_ok(client.post("/api/v1/books", json={"name": "e2e-book"}))
    book_id = book["id"]
    books = _assert_ok(client.get("/api/v1/books", params={"page": 1, "size": 10}))
    assert any(item["id"] == book_id for item in books["items"])
    assert _assert_ok(client.get(f"/api/v1/books/{book_id}"))["name"] == "e2e-book"

    _assert_ok(client.put(f"/api/v1/books/{book_id}", json={"name": "e2e-book-updated"}))
    assert _assert_ok(client.get(f"/api/v1/books/{book_id}"))["name"] == "e2e-book-updated"
    _assert_ok(client.delete(f"/api/v1/books/{book_id}"))
    books = _assert_ok(client.get("/api/v1/books", params={"page": 1, "size": 10}))
    assert all(item["id"] != book_id for item in books["items"])


def _server_env(sql_name: str | None, redis_db: int | None) -> dict[str, str]:
    env = os.environ.copy()
    if sql_name:
        env.update(_SQL_CONFIGS[sql_name].env)
    if redis_db is not None:
        env.update(REDIS_TEST.env(redis_db))
    return env


def _run_generated_project(project: Path, log_dir: Path, env: dict[str, str]) -> None:
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = log_dir / "generated-server.log"
    proc = None
    failure = None
    with log_path.open("w", encoding="utf-8") as log:
        try:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "runserver.py",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--workers",
                    "1",
                    "--log-level",
                    "warning",
                ],
                cwd=str(project),
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            with httpx.Client(base_url=base_url, timeout=5.0) as client:
                _wait_for_health(client)
                _exercise_api(client)
        except Exception as exc:
            failure = exc
        finally:
            if proc is not None:
                _stop_server(proc)

    if failure is not None:
        tail = log_path.read_text("utf-8")[-2000:] if log_path.is_file() else ""
        raise AssertionError(f"{failure}\n--- generated server log ---\n{tail}") from failure


@pytest.mark.parametrize(
    ("new_flags", "sql_name", "redis_db"),
    [
        pytest.param((), None, None, id="sqlite-basic"),
        pytest.param(_OPTIONAL_FLAGS, None, 0, id="sqlite-redis0"),
        pytest.param(("-d", "mysql", *_OPTIONAL_FLAGS), "mysql", 1, id="mysql-redis1"),
        pytest.param(("-d", "postgresql", *_OPTIONAL_FLAGS), "postgresql", 2, id="postgresql-redis2"),
    ],
)
def test_generated_project_api_end_to_end(
    project_workspace: Path,
    run_cli,
    sql_test_databases,
    new_flags,
    sql_name,
    redis_db,
):
    """覆盖脚手架生成、add 子命令以及生成项目在 SQLite / MySQL / PostgreSQL + Redis 下的真实接口。"""
    if sql_name:
        reset_sql_database(_SQL_CONFIGS[sql_name])

    if redis_db is not None:
        client = redis_client(redis_db)
        try:
            client.delete(_SNOW_WORKER_ID_KEY, _SNOW_DATACENTER_ID_KEY)
        finally:
            client.close()

    created = run_cli("new", "demo", *new_flags, cwd=project_workspace)
    assert created.returncode == 0, created.stderr
    project = project_workspace / "demo"

    added = run_cli("add", "book[books]", cwd=project)
    assert added.returncode == 0, added.stderr
    assert (project / "app/api/v1/book.py").is_file()

    _run_generated_project(project, project_workspace, _server_env(sql_name, redis_db))

    if redis_db is not None:
        client = redis_client(redis_db)
        try:
            assert client.get(_SNOW_WORKER_ID_KEY) is not None
        finally:
            client.close()
