"""脚手架命令单元测试：直接测试 `CMD` 的参数校验与模板处理函数。"""

import argparse
import importlib
import os
import sys

import pytest

from fastapi_scaff import __version__


@pytest.fixture(scope="module")
def cli_module():
    # __main__ 导入时会重绑定 sys.stdout/stderr，先替换为带 fileno 的真实文件对象。
    with (
        pytest.MonkeyPatch.context() as mp,
        open(os.devnull, "w", encoding="utf-8") as out,
        open(os.devnull, "w", encoding="utf-8") as err,
    ):
        mp.setattr(sys, "stdout", out)
        mp.setattr(sys, "stderr", err)
        sys.modules.pop("fastapi_scaff.__main__", None)
        module = importlib.import_module("fastapi_scaff.__main__")
    try:
        yield module
    finally:
        sys.modules.pop("fastapi_scaff.__main__", None)


def make_cli_args(command, name, **overrides):
    values = {
        "command": command,
        "name": name,
        "template": "standard",
        "db": "sqlite",
        "loguru": False,
        "redis": False,
        "snow": False,
        "migration": False,
        "celery": False,
        "docker": False,
        "vn": "v1",
        "subdir": "",
        "project": ".",
        "force": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_version_matches_package(cli_module):
    assert cli_module.__version__ == __version__


def test_command_validates_names(cli_module):
    with pytest.raises(SystemExit) as exc:
        cli_module.CMD(make_cli_args("new", "1bad"))
    assert exc.value.code == 1

    with pytest.raises(SystemExit):
        cli_module.CMD(make_cli_args("add", "1bad"))

    with pytest.raises(SystemExit):
        cli_module.CMD(make_cli_args("add", "book[books]", celery=True))

    with pytest.raises(SystemExit):
        cli_module.CMD(make_cli_args("tpl", "unknown"))

    with pytest.raises(SystemExit):
        cli_module.CMD(make_cli_args("tpl", "docker", project="1bad"))

    assert cli_module.CMD(make_cli_args("add", "book[books]")).args.name == "book[books]"


def test_command_normalizes_names(cli_module):
    cmd = cli_module.CMD(make_cli_args("add", " book，article "))
    assert cmd.args.name == "book,article"

    cmd = cli_module.CMD(make_cli_args("add", "book", vn=" v1 ", subdir=" shop "))
    assert (cmd.args.vn, cmd.args.subdir) == ("v1", "shop")


def test_command_dot_uses_current_directory(cli_module, tmp_path, monkeypatch):
    work = tmp_path / "curproj"
    work.mkdir()
    monkeypatch.chdir(work)
    cmd = cli_module.CMD(make_cli_args("new", "."))
    assert cmd.args.name == "curproj"
    assert cmd.args.is_dot is True
    assert os.getcwd() == str(tmp_path)


def test_new_handler_filters_files_and_rewrites_content(cli_module):
    cmd = cli_module.CMD(make_cli_args("new", "demo", template="light"))
    assert cmd._new_handler("docker-swarm.yaml", "x") == (None, None)
    assert cmd._new_handler("nomad-app.hcl", "x") == (None, None)
    assert cmd._new_handler("app/api/v1/user.py", "x") == (None, None)
    assert cmd._new_handler("docs/.gitkeep", "x") == (None, None)

    key, value = cmd._new_handler("pyproject.toml", "[build-system]\n# ===\n[tool.ruff]")
    assert key == "pyproject.toml"
    assert value.startswith("# ===")

    key, value = cmd._new_handler("README.md", "# fastapi-scaff\nbody")
    assert value.startswith("# fastapi-scaff ( => yourProj)")

    key, value = cmd._new_handler("app/core/status.py", "SUCCESS = 1\nUSER_FOO = 2\nkeep = 3\n")
    assert "USER_FOO" not in value and "keep = 3" in value

    key, value = cmd._new_handler("requirements.txt", "alembic==1.20.0\nkeep==1\n")
    assert key == "requirements.txt"
    assert "alembic" not in value and "keep==1" in value


def test_new_db_handler_switches_drivers(cli_module):
    mysql = cli_module.CMD(make_cli_args("new", "demo", db="mysql"))
    env_text = (
        "DB_DRIVERNAME=sqlite\n"
        "DB_ASYNC_DRIVERNAME=sqlite+aiosqlite\n"
        "DB_DATABASE=data/db/app_dev.sqlite3\n"
        "DB_USERNAME=\n"
        "DB_PASSWORD=\n"
        "DB_HOST=\n"
        "DB_PORT=\n"
        "DB_CHARSET=\n"
    )
    _, value = mysql._new_db_handler("config/.env", env_text)
    assert "DB_DRIVERNAME=mysql+pymysql" in value
    _, value = mysql._new_db_handler("requirements.txt", "aiosqlite==0.22.1\n")
    assert "PyMySQL==" in value and "aiomysql==" in value

    none_db = cli_module.CMD(make_cli_args("new", "demo", db="no"))
    assert none_db._new_db_handler("app/core/_db.py", "x") == (None, None)
    assert none_db._new_db_handler("app/models/user.py", "x") == (None, None)
    _, value = none_db._new_db_handler("requirements.txt", "SQLAlchemy==2.1.1\nalembic==1.20.0\nkeep==1\n")
    assert "SQLAlchemy" not in value and "alembic" not in value and "keep==1" in value


def test_add_handler_replaces_snowflake_ids(cli_module):
    source = "import gen_snow_id\nid = mapped_column(BigInteger, primary_key=True, default=gen_snow_id"
    result = cli_module.CMD._add_handler("s_app_models.py", source, True)
    assert "gen_uuid_hex" in result and "String(32)" in result
    assert cli_module.CMD._add_handler("s_app_models.py", source, False) == source


def test_repl_funcs_removes_generated_function(cli_module):
    source = "def helper():\n    return 1\n\nkeep = 2\n"
    result = cli_module.CMD._repl_funcs("helper", source)
    assert "def helper" not in result
    assert isinstance(result, str)


def test_command_tpl_defaults_project_name(cli_module, tmp_path, monkeypatch):
    assert cli_module.CMD(make_cli_args("tpl", "celery")).args.project == "celery_app"
    work = tmp_path / "myproj"
    work.mkdir()
    monkeypatch.chdir(work)
    assert cli_module.CMD(make_cli_args("tpl", "docker")).args.project == "myproj"
