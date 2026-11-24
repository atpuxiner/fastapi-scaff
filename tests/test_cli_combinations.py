"""代表性生成组合测试：从完整参数矩阵中选取主要组合，校验生成结果。"""

import pytest

COMBINATIONS = [
    pytest.param("standard", "sqlite", (), id="standard-sqlite"),
    pytest.param(
        "standard",
        "sqlite",
        ("--loguru", "--redis", "--snow", "--migration", "--celery", "--docker"),
        id="standard-sqlite-all-flags",
    ),
    pytest.param("light", "sqlite", ("--redis", "--snow"), id="light-sqlite-redis-snow"),
    pytest.param("tiny", "sqlite", ("--docker",), id="tiny-sqlite-docker"),
    pytest.param("single", "sqlite", (), id="single-sqlite"),
    pytest.param(
        "standard",
        "mysql",
        ("--loguru", "--redis", "--snow", "--celery"),
        id="standard-mysql-extras",
    ),
    pytest.param(
        "standard",
        "postgresql",
        ("--loguru", "--redis", "--snow", "--celery"),
        id="standard-postgresql-extras",
    ),
    pytest.param(
        "standard",
        "no",
        ("--loguru", "--redis", "--snow", "--celery"),
        id="standard-nodb-extras",
    ),
]


@pytest.mark.parametrize(("template", "db", "flags"), COMBINATIONS)
def test_representative_new_combinations(run_cli, project_workspace, template, db, flags):
    result = run_cli("new", "demo", "-t", template, "-d", db, *flags, cwd=project_workspace)
    assert result.returncode == 0, result.stderr

    root = project_workspace / "demo"
    requirements = (root / "requirements.txt").read_text("utf-8")
    env = (root / "config/.env").read_text("utf-8")
    assert (root / "README.md").is_file()

    if template == "single":
        assert (root / "app/api.py").is_file()
        assert not (root / "app/api").exists()
        assert not (root / "runmigration.py").exists()
        assert "JWT_" not in env and "DB_" not in env
        assert "aiosqlite==" not in requirements
    else:
        assert (root / "app/main.py").is_file()
        if template == "light":
            assert not (root / "app/api/v1/user.py").exists()
            assert not (root / "app/models").exists()
        elif template == "tiny":
            assert not (root / "app/api/v1/user.py").exists()
            assert not (root / "app/services").exists()
        elif db == "no":
            assert not (root / "app/api/v1/user.py").exists()
        else:
            assert (root / "app/api/v1/user.py").is_file()

        if db == "no":
            assert not (root / "app/core/_db.py").exists()
            assert "SQLAlchemy==" not in requirements
        elif db == "mysql":
            assert "PyMySQL==" in requirements and "aiomysql==" in requirements
            assert "DB_DRIVERNAME=mysql+pymysql" in env
        elif db == "postgresql":
            assert "psycopg2-binary==" in requirements and "asyncpg==" in requirements
            assert "DB_DRIVERNAME=postgresql+psycopg2" in env
        else:
            assert "aiosqlite==" in requirements
            assert "DB_DRIVERNAME=sqlite" in env

        log_source = (root / "app/core/_log.py").read_text("utf-8")
        assert ("from toollib.logu import" in log_source) == ("--loguru" in flags)
        assert (root / "app/core/_redis.py").is_file() == ("--redis" in flags)
        assert (root / "app/core/_snow.py").is_file() == ("--snow" in flags)
        assert (root / "app/migrations/alembic.ini").is_file() == ("--migration" in flags)
        assert (root / "celery_app/__init__.py").is_file() == ("--celery" in flags)
        assert (root / "Dockerfile").is_file() == ("--docker" in flags)
        assert ("loguru==" in requirements) == ("--loguru" in flags)
        assert ("redis==" in requirements) == ("--redis" in flags)
        assert ("celery==" in requirements) == ("--celery" in flags)
        assert ("alembic==" in requirements) == ("--migration" in flags)
