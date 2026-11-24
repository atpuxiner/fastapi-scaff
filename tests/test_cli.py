"""脚手架命令测试：通过子进程覆盖 `fastapi-scaff`（python -m fastapi_scaff）的各子命令。"""

import pytest
from fastapi_scaff import __version__


def normalize_path_separators(text: str) -> str:
    """把 Windows 路径分隔符统一成 `/`，便于跨平台断言命令行输出。"""
    return text.replace("\\", "/")


@pytest.fixture
def project(run_cli, project_workspace):
    created = run_cli("new", "demo", cwd=project_workspace)
    assert created.returncode == 0, created.stderr
    return project_workspace / "demo"


def test_no_args_prints_help(run_cli, project_workspace):
    result = run_cli(cwd=project_workspace)
    assert result.returncode == 0
    assert "usage: fastapi-scaff <command> <name> [options]" in result.stdout
    for command in ("new", "add", "tpl"):
        assert command in result.stdout


def test_version(run_cli, project_workspace):
    result = run_cli("--version", cwd=project_workspace)
    assert result.returncode == 0
    assert result.stdout.strip() == f"fastapi-scaff {__version__}"


def test_invalid_arguments(run_cli, project_workspace):
    unknown = run_cli("unknown", "x", cwd=project_workspace)
    assert unknown.returncode == 2
    assert "invalid choice" in unknown.stderr

    empty_name = run_cli("new", "  ", cwd=project_workspace)
    assert empty_name.returncode == 1
    assert "name cannot be empty" in empty_name.stderr

    bad_name = run_cli("new", "1bad", cwd=project_workspace)
    assert bad_name.returncode == 1
    assert "only support regex" in bad_name.stderr

    bad_tpl = run_cli("tpl", "unknown", cwd=project_workspace)
    assert bad_tpl.returncode == 1
    assert "only support" in bad_tpl.stderr

    bad_project = run_cli("tpl", "docker", "-p", "1bad", cwd=project_workspace)
    assert bad_project.returncode == 1
    assert "only support regex" in bad_project.stderr


def test_new_standard_project(run_cli, project_workspace):
    result = run_cli("new", "demo", cwd=project_workspace)
    assert result.returncode == 0, result.stderr
    assert "Starting new project..." in result.stdout
    assert "Done. Now run:" in result.stdout
    assert "cd demo" in result.stdout

    root = project_workspace / "demo"
    for name in (
        "app/main.py",
        "app/api/v1/user.py",
        "app/core/__init__.py",
        "config/.env",
        "requirements.txt",
        "pyproject.toml",
        "README.md",
        "docs/.gitkeep",
        "tests/__init__.py",
        "BuyMeaCoffee.jpg",
    ):
        assert (root / name).is_file(), name
    assert not (root / "single").exists()
    assert not (root / "Dockerfile").exists()
    assert (root / "BuyMeaCoffee.jpg").stat().st_size > 0

    readme = (root / "README.md").read_text("utf-8")
    assert "# fastapi-scaff ( => yourProj)" in readme
    pyproject = (root / "pyproject.toml").read_text("utf-8")
    assert pyproject.startswith("# ===")
    assert "[project]" not in pyproject


def test_new_existing_directory_requires_force(run_cli, project_workspace):
    root = project_workspace / "demo"
    root.mkdir()
    (root / "keep.txt").write_text("keep", encoding="utf-8")

    refused = run_cli("new", "demo", cwd=project_workspace)
    assert refused.returncode == 1
    assert "'demo' already exists" in refused.stderr

    forced = run_cli("new", "demo", "--force", cwd=project_workspace)
    assert forced.returncode == 0, forced.stderr
    assert "will overwrite existing files" in forced.stderr
    assert (root / "app/main.py").is_file()
    assert (root / "keep.txt").read_text("utf-8") == "keep"


def test_new_current_directory(run_cli, project_workspace):
    work = project_workspace / "currentproj"
    work.mkdir()
    result = run_cli("new", ".", cwd=work)
    assert result.returncode == 0, result.stderr
    assert "cd .." in result.stdout
    assert "currentproj" in result.stdout
    assert (work / "app/main.py").is_file()


@pytest.mark.parametrize(
    ("template", "expected", "unexpected"),
    [
        (
            "light",
            ["app/main.py", "app/core/__init__.py"],
            ["app/api/v1/user.py", "app/models/user.py", "app/services/user.py", "docs", "tests", "single"],
        ),
        (
            "tiny",
            ["app/main.py", "app/api/__init__.py"],
            ["app/api/v1/user.py", "app/models", "app/services", "docs", "tests", "single"],
        ),
        (
            "single",
            ["app/main.py", "app/api.py", "app/core.py", "app/middleware.py", "config/.env"],
            ["app/api", "app/models", "app/services", "docs", "tests", "runmigration.py"],
        ),
    ],
)
def test_new_templates(run_cli, project_workspace, template, expected, unexpected):
    result = run_cli("new", "demo", "-t", template, cwd=project_workspace)
    assert result.returncode == 0, result.stderr
    root = project_workspace / "demo"
    for name in expected:
        assert (root / name).exists(), name
    for name in unexpected:
        assert not (root / name).exists(), name
    if template == "single":
        env = (root / "config/.env").read_text("utf-8")
        assert "JWT_" not in env
        assert "SNOW_" not in env
        assert "DB_" not in env
    else:
        assert "alembic==" not in (root / "requirements.txt").read_text("utf-8")


@pytest.mark.parametrize(
    ("db", "present", "absent"),
    [
        ("mysql", ["PyMySQL==1.2.3", "aiomysql==0.3.2", "DB_DRIVERNAME=mysql+pymysql"], ["aiosqlite"]),
        (
            "postgresql",
            ["psycopg2-binary==2.9.13", "asyncpg==0.31.0", "DB_DRIVERNAME=postgresql+psycopg2"],
            ["aiosqlite"],
        ),
    ],
)
def test_new_database_drivers(run_cli, project_workspace, db, present, absent):
    result = run_cli("new", "demo", "-d", db, cwd=project_workspace)
    assert result.returncode == 0, result.stderr
    root = project_workspace / "demo"
    requirements = (root / "requirements.txt").read_text("utf-8")
    env = (root / "config/.env").read_text("utf-8")
    for text in present:
        assert text in requirements or text in env
    for text in absent:
        assert text not in requirements
        assert text not in env


def test_new_without_database(run_cli, project_workspace):
    result = run_cli("new", "demo", "-d", "no", cwd=project_workspace)
    assert result.returncode == 0, result.stderr
    root = project_workspace / "demo"
    for name in ("app/core/_db.py", "app/models/user.py", "app/services/user.py", "app/migrations", "runmigration.py"):
        assert not (root / name).exists(), name
    requirements = (root / "requirements.txt").read_text("utf-8")
    for text in ("SQLAlchemy==", "aiosqlite==", "alembic=="):
        assert text not in requirements
    assert "DB_" not in (root / "config/.env").read_text("utf-8")


def test_new_with_optional_components(run_cli, project_workspace):
    result = run_cli(
        "new",
        "demo",
        "--loguru",
        "--redis",
        "--snow",
        "--migration",
        "--celery",
        "--docker",
        cwd=project_workspace,
    )
    assert result.returncode == 0, result.stderr
    root = project_workspace / "demo"
    for name in (
        "app/core/_log.py",
        "app/core/_redis.py",
        "app/core/_snow.py",
        "app/migrations/alembic.ini",
        "app/api/default/ahealth.py",
        "celery_app/__init__.py",
        "runcbeat.py",
        "runcworker.py",
        "Dockerfile",
        "docker-compose.yaml",
    ):
        assert (root / name).is_file(), name
    requirements = (root / "requirements.txt").read_text("utf-8")
    for package in ("loguru==", "redis==", "alembic==", "celery=="):
        assert package in requirements
    compose = (root / "docker-compose.yaml").read_text("utf-8")
    assert "demo" in compose
    assert "fastapi-scaff" not in compose


def test_add_standard_api(run_cli, project):
    result = run_cli("add", "book[books]", cwd=project)
    assert result.returncode == 0, result.stderr
    assert "Adding api:" in result.stdout
    assert "[add] Writing app/api/v1/book.py" in normalize_path_separators(result.stdout)

    api = (project / "app/api/v1/book.py").read_text("utf-8")
    models = (project / "app/models/book.py").read_text("utf-8")
    assert 'path="/books"' in api
    assert "@router.get" in api
    assert "tpl" not in api.lower()
    assert "class Book" in models
    assert '__tablename__ = "books"' in models
    assert (project / "app/services/book.py").is_file()


def test_add_multiple_apis_with_chinese_comma(run_cli, project):
    result = run_cli("add", "book，article", cwd=project)
    assert result.returncode == 0, result.stderr
    for name in ("book", "article"):
        assert (project / f"app/api/v1/{name}.py").is_file()
        assert (project / f"app/services/{name}.py").is_file()
        assert (project / f"app/models/{name}.py").is_file()


def test_add_existing_api_requires_force(run_cli, project):
    first = run_cli("add", "book", cwd=project)
    assert first.returncode == 0, first.stderr

    second = run_cli("add", "book", cwd=project)
    assert second.returncode == 0
    assert "[add] Existed app/api/v1/book.py" in normalize_path_separators(second.stderr)
    assert "use --force" in second.stderr
    assert "[add] Writing" not in second.stdout

    forced = run_cli("add", "book", "--force", cwd=project)
    assert forced.returncode == 0, forced.stderr
    assert "[add] Overwriting app/api/v1/book.py" in normalize_path_separators(forced.stdout)


def test_add_creates_new_version_dir_after_prompt(run_cli, project):
    result = run_cli("add", "book", "-v", "v2", cwd=project, stdin="y\n")
    assert result.returncode == 0, result.stderr
    assert "app/api/v2 not exists, create? [y/n]" in normalize_path_separators(result.stdout)
    init_file = project / "app/api/v2/__init__.py"
    assert init_file.is_file()
    assert '_prefix = "/api/v2"' in init_file.read_text("utf-8")
    assert (project / "app/api/v2/book.py").is_file()

    rejected = run_cli("add", "article", "-v", "v3", cwd=project, stdin="n\n")
    assert rejected.returncode == 1
    assert not (project / "app/api/v3").exists()
    assert not (project / "app/services/article.py").exists()


def test_add_with_subdir(run_cli, project):
    result = run_cli("add", "book", "-s", "shop", cwd=project)
    assert result.returncode == 0, result.stderr
    init_file = project / "app/api/v1/shop/__init__.py"
    assert init_file.is_file()
    assert '_prefix = "/shop"' in init_file.read_text("utf-8")
    assert (project / "app/api/v1/shop/book.py").is_file()
    assert (project / "app/services/shop/book.py").is_file()
    assert (project / "app/models/shop/book.py").is_file()
    api = (project / "app/api/v1/shop/book.py").read_text("utf-8")
    assert "from app.services.shop.book import" in api
    assert "from app.models.shop.book import" in api


@pytest.mark.parametrize(
    ("dirs", "expected", "unexpected"),
    [
        (["app/api", "app/services"], ["app/api/v1/book.py", "app/services/book.py"], ["app/models/book.py"]),
        (["app/api"], ["app/api/v1/book.py"], ["app/services/book.py", "app/models/book.py"]),
    ],
)
def test_add_detects_target_by_existing_dirs(run_cli, project_workspace, dirs, expected, unexpected):
    work = project_workspace / "bare"
    for name in dirs:
        (work / name).mkdir(parents=True)
    result = run_cli("add", "book", cwd=work, stdin="y\n")
    assert result.returncode == 0, result.stderr
    for name in expected:
        assert (work / name).is_file(), name
    for name in unexpected:
        assert not (work / name).exists(), name


def test_add_rejects_invalid_names(run_cli, project):
    bad_name = run_cli("add", "1bad", cwd=project)
    assert bad_name.returncode == 1
    assert "only support regex" in bad_name.stderr

    plural_with_celery = run_cli("add", "book[books]", "--celery", cwd=project)
    assert plural_with_celery.returncode == 1

    empty_vn = run_cli("add", "book", "-v", " ", cwd=project)
    assert empty_vn.returncode == 1
    assert "vn cannot be empty" in empty_vn.stderr

    bad_subdir = run_cli("add", "book", "-s", "bad-name", cwd=project)
    assert bad_subdir.returncode == 1
    assert "only support regex" in bad_subdir.stderr


def test_tpl_docker(run_cli, project_workspace):
    result = run_cli("tpl", "docker", "-p", "myproj", cwd=project_workspace)
    assert result.returncode == 0, result.stderr
    assert "tpl myproj:" in result.stdout
    for name in (".dockerignore", "docker-build.sh", "Dockerfile", "Dockerfile-bullseye", "docker-compose.yaml"):
        assert (project_workspace / name).is_file(), name
    compose = (project_workspace / "docker-compose.yaml").read_text("utf-8")
    assert "myproj" in compose
    assert "fastapi-scaff" not in compose
    dockerfile = (project_workspace / "Dockerfile").read_text("utf-8")
    assert "fastapi-scaff" not in dockerfile

    refused = run_cli("tpl", "docker", "-p", "myproj", cwd=project_workspace)
    assert refused.returncode == 0
    assert "[tpl] Existed" in refused.stdout
    assert "use --force" in refused.stdout

    forced = run_cli("tpl", "docker", "-p", "myproj", "--force", cwd=project_workspace)
    assert forced.returncode == 0, forced.stderr
    assert "[tpl] Overwrite" in forced.stdout


@pytest.mark.parametrize(
    ("name", "expected", "placeholder_files", "unexpected"),
    [
        ("swarm", ["docker-swarm.yaml"], ["docker-swarm.yaml"], ["nomad-app.hcl"]),
        (
            "nomad",
            ["nomad-setup.sh", "nomad-traefik.hcl", "nomad-app.hcl"],
            ["nomad-app.hcl"],
            ["Dockerfile"],
        ),
    ],
)
def test_tpl_swarm_and_nomad(run_cli, project_workspace, name, expected, placeholder_files, unexpected):
    result = run_cli("tpl", name, "-p", "myproj", cwd=project_workspace)
    assert result.returncode == 0, result.stderr
    for filename in expected:
        assert (project_workspace / filename).is_file()
    for filename in placeholder_files:
        content = (project_workspace / filename).read_text("utf-8")
        assert "myproj" in content
        assert "fastapi-scaff" not in content
    for filename in unexpected:
        assert not (project_workspace / filename).exists()


def test_tpl_celery(run_cli, project_workspace):
    result = run_cli("tpl", "celery", cwd=project_workspace)
    assert result.returncode == 0, result.stderr
    assert (project_workspace / "celery_app/__init__.py").is_file()
    assert (project_workspace / "celery_app/producer/publisher.py").is_file()
    assert (project_workspace / "celery_app/consumer/tasks/health.py").is_file()
    assert (project_workspace / "runcbeat.py").is_file()
    assert (project_workspace / "runcworker.py").is_file()

    refused = run_cli("tpl", "celery", cwd=project_workspace)
    assert refused.returncode == 0
    assert "[tpl] Existed celery_app" in refused.stdout

    forced = run_cli("tpl", "celery", "--force", cwd=project_workspace)
    assert forced.returncode == 0, forced.stderr
    assert "[tpl] Overwrite celery_app" in forced.stdout

    reserved = run_cli("tpl", "celery", "-p", "celery", cwd=project_workspace)
    assert reserved.returncode == 0
    assert "Cannot use reserved name 'celery'" in reserved.stdout

    bad_name = run_cli("tpl", "celery", "-p", "bad-name", cwd=project_workspace)
    assert bad_name.returncode == 1
    assert "only support regex" in bad_name.stderr


def test_tpl_default_project_uses_current_directory(run_cli, project_workspace):
    work = project_workspace / "myproj"
    work.mkdir()
    result = run_cli("tpl", "docker", cwd=work)
    assert result.returncode == 0, result.stderr
    assert "tpl myproj:" in result.stdout
    assert "myproj" in (work / "docker-compose.yaml").read_text("utf-8")
