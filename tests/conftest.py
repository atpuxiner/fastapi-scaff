"""测试公共夹具。"""

import importlib
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.db_config import (  # noqa: E402
    MYSQL_TEST,
    POSTGRES_TEST,
    REDIS_TEST,
    ensure_mysql_database,
    ensure_postgres_database,
    redis_clients,
)

DEFAULT_TEST_PROJECTS_DIR = "data/tests"


def pytest_addoption(parser):
    """注册测试项目生成目录选项，默认写入项目根目录下的 data/tests/。"""
    parser.addoption(
        "--test-projects-dir",
        action="store",
        default=os.getenv("TEST_PROJECTS_DIR", DEFAULT_TEST_PROJECTS_DIR),
        help="Directory where CLI tests generate projects (default: data/tests/).",
    )


@pytest.fixture(scope="session")
def isolated_app(tmp_path_factory):
    """会话内只加载一次应用，避免真实 Redis / 项目日志与数据文件副作用。"""
    import app.core as core

    original_state = dict(core.g.__dict__)
    with pytest.MonkeyPatch.context() as mp:
        db_dir = tmp_path_factory.mktemp("app-db")
        mp.setenv("APP_ENV", "test")
        mp.setenv("APP_DISABLE_DOCS", "false")
        mp.setenv("APP_LOG_ENABLE_FILE", "false")
        mp.setenv("DB_DATABASE", str(db_dir / "app_test.sqlite3"))
        mp.setattr(core, "init_snow_cli", lambda **kwargs: object())
        core.g.setup(force=True)
        sys.modules.pop("app.main", None)
        app_module = importlib.import_module("app.main")

    yield app_module.app

    core.g.__dict__.clear()
    core.g.__dict__.update(original_state)
    sys.modules.pop("app.main", None)


@pytest.fixture
def client(isolated_app):
    with TestClient(isolated_app) as test_client:
        yield test_client
    isolated_app.dependency_overrides.clear()


@pytest.fixture
def run_cli():
    """以子进程运行 `python -m fastapi_scaff`，覆盖真实命令行入口行为。"""

    def _run(*args, cwd: Path, stdin: str | None = None, **kwargs):
        env = os.environ.copy()
        pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(PROJECT_ROOT) + (os.pathsep + pythonpath if pythonpath else "")
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "-m", "fastapi_scaff", *(str(a) for a in args)],
            cwd=str(cwd),
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            **kwargs,
        )

    return _run


@pytest.fixture(scope="session")
def test_projects_dir(pytestconfig) -> Path:
    """测试项目生成根目录，可通过 --test-projects-dir 或环境变量指定。"""
    path = Path(pytestconfig.getoption("test_projects_dir")).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def test_run_dir(test_projects_dir) -> Path:
    """本次测试运行的独立目录：时间串 + 短 uuid。"""
    path = test_projects_dir / f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def project_workspace(request, test_run_dir) -> Path:
    """为单个用例在本次运行目录下分配独立子目录。"""
    module = request.module.__name__.rsplit(".", 1)[-1]
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.name).strip("._") or "case"
    workspace = test_run_dir / f"{module}_{name}"
    workspace.mkdir(parents=True)
    return workspace


@pytest.fixture(scope="session")
def postgres_test_config():
    return POSTGRES_TEST


@pytest.fixture(scope="session")
def mysql_test_config():
    return MYSQL_TEST


@pytest.fixture(scope="session")
def redis_test_config():
    return REDIS_TEST


@pytest.fixture(scope="session")
def sql_test_databases():
    """确保 PostgreSQL / MySQL 的 tests 库存在，供需要的用例直接使用。"""
    ensure_postgres_database()
    ensure_mysql_database()
    return POSTGRES_TEST, MYSQL_TEST


@pytest.fixture(scope="session")
def redis_test_clients():
    """返回 Redis 0/1/2 库客户端，会话结束后关闭连接。"""
    clients = redis_clients()
    try:
        yield clients
    finally:
        for client in clients.values():
            client.close()
