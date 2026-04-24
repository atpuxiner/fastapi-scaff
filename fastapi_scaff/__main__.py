"""
@author axiner
@version v1.0.0
@created 2024/07/29 22:22
@abstract
@description
@history
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

from fastapi_scaff import __version__

sys.stdout = os.fdopen(sys.stdout.fileno(), "w", buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", buffering=1)

here = Path(__file__).resolve().parent
prog = "fastapi-scaff"


def main():
    parser = argparse.ArgumentParser(
        prog=prog,
        usage="%(prog)s <command> <name> [options]",
        description="FastAPI scaffolding tool — generate project or API endpoints instantly to simplify development.",
        epilog="""
examples:
  New project:                      fastapi-scaff new myproj
  New project with DB & Redis:      fastapi-scaff new myproj -d postgresql --redis
  New project with . & force:       fastapi-scaff new . --force
  Add an API endpoint:              fastapi-scaff add myapi[myapis]
  Add multiple APIs:                fastapi-scaff add myapi1[myapi1s],myapi2[myapi2s] -s myapi
  
  💡 Tip:
    1. Project Naming Convention
    - Use '.' to denote current directory as project name. Use --force if not empty.

    2. API Naming Convention
    The plural form in square brackets [myapis] is used for:
    - RESTful URL paths (e.g., /api/v1/myapis)
    - Database table names (e.g., myapis table)
    If no plural form is specified, singular and plural will be the same.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "command", choices=["new", "add"], help="Subcommand: 'new' to new a project, 'add' to add API(s)"
    )
    parser.add_argument("name", type=str, help="Project name or API name(s) (multiple APIs can be comma-separated)")
    parser.add_argument(
        "-t",
        "--template",
        default="standard",
        choices=["standard", "light", "tiny", "single"],
        metavar="",
        help="(new) Specify project template (default: standard)",
    )
    parser.add_argument(
        "-d",
        "--db",
        default="sqlite",
        choices=["sqlite", "mysql", "postgresql", "no"],
        metavar="",
        help="(new) Specify database (default: sqlite; 'no' means no integration)",
    )
    parser.add_argument("--loguru", action="store_true", help="(new) Specify loguru (default: logging)")
    parser.add_argument("--redis", action="store_true", help="(new) Specify Redis (default: no)")
    parser.add_argument("--snow", action="store_true", help="(new) Specify Snowflake (default: no)")
    parser.add_argument("--migration", action="store_true", help="(new) Specify migration (default: no)")
    parser.add_argument(
        "-v", "--vn", default="v1", type=str, metavar="", help="(add) Specify API version for the API (default: v1)"
    )
    parser.add_argument(
        "-s",
        "--subdir",
        default="",
        type=str,
        metavar="",
        help="(add) Specify subdirectory for the API (default: none)",
    )
    parser.add_argument("--celery", action="store_true", help="(new|add) Specify Celery (default: no)")
    parser.add_argument("--force", action="store_true", help="(new|add) Force overwrite")
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    args = parser.parse_args()
    cmd = CMD(args)
    if args.command == "new":
        cmd.new()
    else:
        cmd.add()


class CMD:
    def __init__(self, args: argparse.Namespace):
        args.name = args.name.replace(" ", "")
        if not args.name:
            sys.stderr.write(f"{prog}: name cannot be empty\n")
            sys.exit(1)
        if args.command == "new":
            args.is_dot = args.name == "."
            if args.is_dot:
                args.name = Path.cwd().name
                os.chdir("..")
            pattern = r"^[A-Za-z][A-Za-z0-9_-]{0,64}$"
            if not re.search(pattern, args.name):
                sys.stderr.write(f"{prog}: '{args.name}' only support regex: {pattern}\n")
                sys.exit(1)
        else:
            pattern = r"^[A-Za-z][A-Za-z0-9_]{0,64}(\[[A-Za-z][A-Za-z0-9_]{0,69}\])?$"
            if args.celery:
                pattern = r"^[A-Za-z][A-Za-z0-9_]{0,64}$"
            args.name = args.name.replace("，", ",").strip(",")
            for t in args.name.split(","):
                if not re.search(pattern, t):
                    sys.stderr.write(f"{prog}: '{t}' only support regex: {pattern}\n")
                    sys.exit(1)
            args.vn = args.vn.replace(" ", "")
            if not args.vn:
                sys.stderr.write(f"{prog}: vn cannot be empty\n")
                sys.exit(1)
            if not re.search(pattern, args.vn):
                sys.stderr.write(f"{prog}: '{args.vn}' only support regex: {pattern}\n")
                sys.exit(1)
            args.subdir = args.subdir.replace(" ", "")
            if args.subdir and not re.search(pattern, args.subdir):
                sys.stderr.write(f"{prog}: '{args.subdir}' only support regex: {pattern}\n")
                sys.exit(1)
        self.args = args

    def new(self):
        sys.stdout.write("Starting new project...\n")
        name = Path(self.args.name)
        _show_name = f"..{os.sep}{name}" if self.args.is_dot else name
        if name.is_dir() and any(name.iterdir()):
            if self.args.force:
                sys.stderr.write(f"{prog}: '{_show_name}' already exists, will overwrite existing files\n")
            else:
                sys.stderr.write(f"{prog}: '{_show_name}' already exists\n")
                sys.exit(1)
        name.mkdir(parents=True, exist_ok=True)
        with open(here.joinpath("_project_tpl.json"), "r") as f:
            project_tpl = json.loads(f.read())
        base64_suffixes = (".jpg",)
        for k, v in project_tpl.items():
            base64_flag = k.endswith(base64_suffixes)
            if not base64_flag:
                k, v = self._tpl_handler(k, v)
            if k:
                tplpath = name.joinpath(k)
                tplpath.parent.mkdir(parents=True, exist_ok=True)
                if base64_flag:
                    with open(tplpath, "wb") as f:
                        f.write(base64.b64decode(v))
                else:
                    with open(tplpath, "w", encoding="utf-8") as f:
                        f.write(v)
        sys.stdout.write(
            "Done. Now run:\n"
            f"> 1. cd {_show_name}\n"
            f"> 2. modify config{'' if (self.args.template == 'single' or self.args.db == 'no') else ', eg: db'}\n"
            f"> 3. pip install -r requirements.txt\n"
            f"> 4. python runserver.py\n"
            f"----- More see README.md -----\n"
        )

    def _tpl_handler(self, k: str, v: str):
        for c, h in [
            (self.args.celery is False, self._tpl_celery_handler),
            (1, self._tpl_template_handler),
            (1, self._tpl_db_handler),
            (self.args.loguru is False, self._tpl_loguru_handler),
            (self.args.redis is False, self._tpl_redis_handler),
            (self.args.snow is False, self._tpl_snow_handler),
            (self.args.migration is False, self._tpl_migration_handler),
        ]:
            if c:
                k, v = h(k, v)
                if not k:
                    return k, v

        if not k:
            return k, v

        if k == "config/nginx.conf":
            v = v.replace("server backend:", f"server {self.args.name.replace('_', '-')}-prod_backend:")
        elif k.startswith(
            (
                "build.sh",
                "docker-compose.",
            )
        ):
            v = v.replace("fastapi-scaff", self.args.name.replace("_", "-"))
        elif k == "README.md":
            v = v.replace(f"# {prog}", f"# {prog} ( => yourProj)")
        return k, v

    def _tpl_celery_handler(self, k, v):
        if k in {
            "app/api/default/aping.py",
            "runcbeat.py",
            "runcworker.py",
        } or k.startswith("app_celery/"):
            k, v = None, None
        elif k == "requirements.txt":
            v = re.sub(r"^celery==.*$\n?", "", v, flags=re.MULTILINE)
        elif _ := re.search(r"config/app_(.*).yaml$", k):
            v = re.sub(r"^\s*# #\s*\n(?:^\s*CELERY_.*$\n?)+", "", v, flags=re.MULTILINE)
        return k, v

    def _tpl_template_handler(self, k, v):
        if self.args.template == "standard":
            if k.startswith(("single/",)):
                return None, None
            return k, v
        elif self.args.template == "light":
            if (
                re.match(
                    r"^({filter_k})".format(
                        filter_k="|".join(
                            [
                                "app/api/v1/user.py",
                                "app/models/",
                                "app/services/user.py",
                                "docs/",
                                "tests/",
                                "single/",
                            ]
                        )
                    ),
                    k,
                )
                is not None
            ):
                return None, None
            elif k == "app/core/_db.py":
                v = (
                    v.replace('_MODELS_MOD_DIR = APP_DIR.joinpath("models")', "_MODELS_MOD_DIR = None")
                    .replace('_MODELS_MOD_BASE = "app.models"', "_MODELS_MOD_BASE = None")
                    .replace('_DECL_BASE_NAME = "DeclBase"', "_DECL_BASE_NAME = None")
                )
            elif k == "app/core/status.py":
                v = re.sub(r"^\s*USER_.*$\n?", "", v, flags=re.MULTILINE)
            elif k == "requirements.txt":
                v = re.sub(r"^alembic==.*$\n?", "", v, flags=re.MULTILINE)
            return k, v
        elif self.args.template == "tiny":
            if (
                re.match(
                    r"^({filter_k})".format(
                        filter_k="|".join(
                            [
                                "app/api/v1/user.py",
                                "app/models/",
                                "app/services/",
                                "docs/",
                                "tests/",
                                "single/",
                            ]
                        )
                    ),
                    k,
                )
                is not None
            ):
                return None, None
            elif k == "app/core/_db.py":
                v = (
                    v.replace('_MODELS_MOD_DIR = APP_DIR.joinpath("models")', "_MODELS_MOD_DIR = None")
                    .replace('_MODELS_MOD_BASE = "app.models"', "_MODELS_MOD_BASE = None")
                    .replace('_DECL_BASE_NAME = "DeclBase"', "_DECL_BASE_NAME = None")
                )
            elif k == "app/core/status.py":
                v = re.sub(r"^\s*USER_.*$\n?", "", v, flags=re.MULTILINE)
            elif k == "requirements.txt":
                v = re.sub(r"^alembic==.*$\n?", "", v, flags=re.MULTILINE)
            return k, v
        else:
            if (
                re.match(
                    r"^({filter_k})".format(
                        filter_k="|".join(
                            [
                                "app/",
                                "docs/",
                                "tests/",
                                "runmigration.py",
                            ]
                        )
                    ),
                    k,
                )
                is not None
            ):
                return None, None
            elif k.startswith("single/"):
                k = k.replace("single/", "")
            elif k == "config/.env":
                v = re.sub(r"(?:^[ \t]*#[^\n]*\n)*^[ \t]*(JWT_|SNOW_)[^\n]*\n?", "", v, flags=re.MULTILINE)
            elif re.search(r"config/app_(.*).yaml$", k):
                v = re.sub(r"^\s*# #\s*\n(?:^\s*DB_.*$\n?)+", "", v, flags=re.MULTILINE)
            elif k == "requirements.txt":
                v = re.sub(r"^(PyJWT==|bcrypt==|SQLAlchemy==|alembic==|aiosqlite==).*$\n?", "", v, flags=re.MULTILINE)
            return k, v

    def _tpl_db_handler(self, k, v):
        if self.args.db == "no":
            if (
                k
                in {
                    "app/core/_db.py",
                    "runmigration.py",
                }
                or k.startswith("app/migrations/")
                or k.endswith("user.py")
            ):
                return None, None
            elif k == "app/api/deps.py":
                v = re.sub(r"^from.*sqlalchemy.*$\n?", "", v, flags=re.MULTILINE)
                v = re.sub(r"\n\s*# 建议：jwt_key进行redis缓存.*?(?=\n\s*\n|$)", "", v, flags=re.DOTALL)
            elif k == "app/core/__init__.py":
                v = re.sub(r"^from.*(sqlalchemy|_db).*$\n?", "", v, flags=re.MULTILINE)
                v = re.sub(r'^\s*(?:#\s*)?"db_async_session",?\s*\n', "", v, flags=re.MULTILINE)
                v = self._repl_funcs(func_names="db_async_session", v=v)
            elif k == "app/core/_conf.py":
                v = re.sub(r"^\s*DB_.*$\n?", "", v, flags=re.MULTILINE)
                v = re.sub(r"^\s*# #[ \t]*\n(?=\s*\n)", "", v, flags=re.MULTILINE)
            elif k == "app/core.py":
                v = re.sub(r"^from.*sqlalchemy.*$\n?", "", v, flags=re.MULTILINE)
                v = re.sub(r"^\s*DB_.*$\n?", "", v, flags=re.MULTILINE)
                v = self._repl_funcs(func_names="(init_db_async_session|make_db_url|db_async_session)", v=v)
                v = re.sub(r'^\s*(?:#\s*)?"db_async_session",?\s*\n', "", v, flags=re.MULTILINE)
                v = re.sub(r"^\s*# #[ \t]*\n(?=\s*\n)", "", v, flags=re.MULTILINE)
            elif k == "app/models/__init__.py":
                v = '"""\n数据模型\n"""\n'
            elif k == "app/services/__init__.py":
                v = '"""\n业务逻辑\n"""\n'
            elif re.search(r"config/app_(.*).yaml$", k):
                v = re.sub(r"^\s*# #\s*\n(?:^\s*DB_.*$\n?)+", "", v, flags=re.MULTILINE)
            elif k == "requirements.txt":
                v = re.sub(r"^(SQLAlchemy==|alembic==|aiosqlite==).*$\n?", "", v, flags=re.MULTILINE)
            return k, v

        if env := re.search(r"config/app_(.*).yaml$", k):
            ov = f"DB_DRIVERNAME: sqlite\nDB_ASYNC_DRIVERNAME: sqlite+aiosqlite\nDB_DATABASE: app_{env.group(1)}.sqlite\nDB_USERNAME:\nDB_PASSWORD:\nDB_HOST:\nDB_PORT:\nDB_CHARSET:"
            if self.args.db == "mysql":
                nv = "DB_DRIVERNAME: mysql+pymysql\nDB_ASYNC_DRIVERNAME: mysql+aiomysql\nDB_DATABASE: <database>\nDB_USERNAME: <username>\nDB_PASSWORD: <password>\nDB_HOST: <host>\nDB_PORT: <port>\nDB_CHARSET: utf8mb4"
                v = v.replace(ov, nv)
            elif self.args.db == "postgresql":
                nv = "DB_DRIVERNAME: postgresql+psycopg2\nDB_ASYNC_DRIVERNAME: postgresql+asyncpg\nDB_DATABASE: <database>\nDB_USERNAME: <username>\nDB_PASSWORD: <password>\nDB_HOST: <host>\nDB_PORT: <port>\nDB_CHARSET:"
                v = v.replace(ov, nv)
        elif k == "requirements.txt":
            if self.args.db == "mysql":
                mysql = [
                    "PyMySQL==1.1.2",
                    "aiomysql==0.3.2",
                ]
                v = re.sub(r"^aiosqlite==.*$\n?", "\n".join(mysql) + "\n", v, flags=re.MULTILINE)
            elif self.args.db == "postgresql":
                postgresql = [
                    "psycopg2-binary==2.9.12",
                    "asyncpg==0.31.0",
                ]
                v = re.sub(r"^aiosqlite==.*$\n?", "\n".join(postgresql) + "\n", v, flags=re.MULTILINE)
        return k, v

    def _tpl_loguru_handler(self, k, v):
        if k in (
            "app/core/_log.py",
            "core.py",
            "main.py",
        ):
            v = v.replace("from toollib.logu", "from toollib.log")
        elif k == "requirements.txt":
            v = re.sub(r"^loguru==.*$\n?", "", v, flags=re.MULTILINE)
        return k, v

    def _tpl_redis_handler(self, k, v):
        if k == "app/core/_redis.py":
            k, v = None, None
        elif k == "app/core/__init__.py":
            v = re.sub(r"^\s*from\s+.*?(Redis|_redis).*?$\n?", "", v, flags=re.MULTILINE)
            v = re.sub(r'^\s*(?:#\s*)?"redis_cli",?\s*\n', "", v, flags=re.MULTILINE)
            v = self._repl_funcs(func_names="redis_cli", v=v)
        elif k == "app/core/_conf.py" or re.search(r"config/app_(.*).yaml$", k):
            v = re.sub(r"^\s*REDIS_.*$\n?", "", v, flags=re.MULTILINE)
        elif k == "app/core.py":
            v = re.sub(r"^\s*from\s+.*?(Redis|_redis).*?$\n?", "", v, flags=re.MULTILINE)
            v = re.sub(r'^\s*(?:#\s*)?"redis_cli",?\s*\n', "", v, flags=re.MULTILINE)
            v = self._repl_funcs(func_names="(init_redis_cli|redis_cli)", v=v)
            v = re.sub(r"^\s*REDIS_(?!cli).*$\n?", "", v, flags=re.MULTILINE)
        elif k == "requirements.txt" and not self.args.celery:
            v = re.sub(r"^redis==.*$\n?", "", v, flags=re.MULTILINE)
        return k, v

    def _tpl_snow_handler(self, k, v):
        if k == "app/api/deps.py":
            v = v.replace('params={"id": int(user_id)}', 'params={"id": user_id}')
        elif k == "app/core/_snow.py":
            return None, None
        elif k == "app/core/__init__.py":
            v = re.sub(r"^\s*from\s+.*?(Snow|_snow).*?$\n?", "", v, flags=re.MULTILINE)
            v = re.sub(r'^\s*(?:#\s*)?"snow_cli",?\s*\n', "", v, flags=re.MULTILINE)
            v = self._repl_funcs(func_names="snow_cli", v=v)
        elif k == "app/core/_conf.py":
            v = re.sub(r"^\s*SNOW_.*$\n?", "", v, flags=re.MULTILINE)
        elif k == "app/models/user.py":
            v = re.sub(r"^\s*from\s+.*?core.*?$\n?", "", v, flags=re.MULTILINE)
            v = v.replace("import gen_snow_id", "import gen_uuid_hex").replace(
                "id = mapped_column(BigInteger, primary_key=True, default=gen_snow_id",
                "id = mapped_column(String(32), primary_key=True, default=gen_uuid_hex",
            )
        elif k == "app/services/user.py":
            v = re.sub(r'^\s*converters={"id": str},*$\n?', "", v, flags=re.MULTILINE)
            v = v.replace('str(result.data["id"])', 'result.data["id"]').replace(
                'where={"id": int(user_id)},', 'where={"id": user_id},'
            )
        elif k == "app/utils/ext_util.py":
            v = re.sub(r"^\s*from\s+.*?core.*?$\n?", "", v, flags=re.MULTILINE)
            v = self._repl_funcs(func_names="gen_snow_id", v=v)
        elif k == "app/core.py":
            v = re.sub(r"^\s*from\s+.*?(Snow|_snow).*?$\n?", "", v, flags=re.MULTILINE)
            v = re.sub(r'^\s*(?:#\s*)?"snow_cli",?\s*\n', "", v, flags=re.MULTILINE)
            v = self._repl_funcs(func_names="(init_snow_cli|_snow_incr|snow_cli)", v=v)
            v = re.sub(r"^\s*SNOW_.*$\n?", "", v, flags=re.MULTILINE)
            v = re.sub(r"^\s*_CACHE_.*$\n?", "", v, flags=re.MULTILINE)
            v = v.replace("Singleton, localip", "Singleton")
        elif k == "config/.env":
            v = re.sub(r"(?:^[ \t]*#[^\n]*\n)*^[ \t]*SNOW_[^\n]*\n?", "", v, flags=re.MULTILINE)
        return k, v

    def _tpl_migration_handler(self, k, v):
        if k.startswith(("app/migrations/", "runmigration.py")):
            return None, None
        return k, v

    @staticmethod
    def _repl_funcs(func_names: str, v: str, repl: str = "") -> str:
        return re.sub(
            rf"^(\s*@[^\n]*\n)*\s*def\s+{func_names}\s*\([^)]*\)(?:\s*->\s*[\w.]+)?\s*:\n(?:\s+.*\n)*?(?=\n+\s+\S+|\Z)",
            repl,
            v,
            flags=re.MULTILINE,
        )

    def add(self):
        if self.args.celery:
            return self._add_celery_handler(self.args.name.split(","))
        vn = self.args.vn
        subdir = self.args.subdir

        work_dir = Path.cwd()
        with open(here.joinpath("_api_tpl.json"), "r", encoding="utf-8") as f:
            api_tpl_dict = json.loads(f.read())

        target, tpl_mods = (
            "s",
            [
                "app/api",
                "app/services",
                "app/models",
            ],
        )
        if not work_dir.joinpath("app/models").is_dir():
            target, tpl_mods = (
                "l",
                [
                    "app/api",
                    "app/services",
                ],
            )
            if not work_dir.joinpath("app/services").is_dir():
                target, tpl_mods = (
                    "t",
                    [
                        "app/api",
                    ],
                )
        nodeclorm = True
        declorm_file = work_dir.joinpath("app/models/__init__.py")
        if declorm_file.is_file() and re.search(
            r"^\s*class\s+DeclBase\s*\(\s*DeclarativeBase, CRUDMixin\s*\)\s*:",
            declorm_file.read_text("utf-8"),
            re.MULTILINE,
        ):
            nodeclorm = False
        nosnow = True
        snow_file = Path("app/utils/ext_util.py")
        if snow_file.is_file() and "def gen_snow_id" in snow_file.read_text("utf-8"):
            nosnow = False
        for mod in tpl_mods:
            if not work_dir.joinpath(mod).is_dir():
                sys.stderr.write(f"[error] Not exists: {mod.replace('/', os.sep)}\n")
                sys.exit(1)
        for name in self.args.name.split(","):
            if "[" in name:
                name_parts = name.split("[")
                name = name_parts[0]
                names = name_parts[-1].rstrip("]")
            else:
                names = name
            sys.stdout.write("Adding api:\n")
            if not self.args.force:
                existed_file = None
                for mod in tpl_mods:
                    if mod == "app/api":
                        mod = f"{mod}/{vn}"
                    if subdir:
                        mod = f"{mod}/{subdir}"
                    curr_mod_file = work_dir.joinpath(mod, name + ".py")
                    if curr_mod_file.is_file():
                        existed_file = curr_mod_file
                        break
                if existed_file:
                    sys.stderr.write(
                        f"[{name}] Existed {existed_file.relative_to(work_dir)}. Operation cancelled, please handle manually.\n"
                    )
                    continue
            for mod in tpl_mods:
                # dir
                curr_mod_dir = work_dir.joinpath(mod)
                if mod.endswith("api"):
                    # vn dir
                    curr_mod_dir = curr_mod_dir.joinpath(vn)
                    if not curr_mod_dir.is_dir():
                        curr_mod_dir_rel = curr_mod_dir.relative_to(work_dir)
                        is_create = input(f"{curr_mod_dir_rel} not exists, create? [y/n]: ")
                        if is_create.lower() == "y" or is_create == "":
                            try:
                                curr_mod_dir.mkdir(parents=True, exist_ok=True)
                                with open(curr_mod_dir.joinpath("__init__.py"), "w", encoding="utf-8") as f:
                                    f.write(f"""\"\"\"\napi-{vn}\n\"\"\"\n\n_prefix = "/api/{vn}"\n""")
                            except Exception as e:
                                sys.stderr.write(f"[{name}] Failed create {curr_mod_dir_rel}: {e}\n")
                                sys.exit(1)
                        else:
                            sys.exit(1)
                if subdir:
                    curr_mod_dir = curr_mod_dir.joinpath(subdir)
                    curr_mod_dir.mkdir(parents=True, exist_ok=True)
                    with open(curr_mod_dir.joinpath("__init__.py"), "w", encoding="utf-8") as f:
                        f.write("")
                        if mod.endswith("api"):
                            f.write(f"""\"\"\"\n{subdir}\n\"\"\"\n\n_prefix = "/{subdir}"\n""")
                # file
                curr_mod_file = curr_mod_dir.joinpath(name + ".py")
                _is_existed = curr_mod_file.is_file()
                with open(curr_mod_file, "w", encoding="utf-8") as f:
                    sys.stdout.write(
                        f"[{name}] {'Overwriting' if _is_existed else 'Writing'} {curr_mod_file.relative_to(work_dir)}\n"
                    )
                    k = f"{target}_{mod.replace('/', '_')}.py"
                    if target == "s" and nodeclorm:
                        k = f"{k[:-3]}_nodeclorm.py"
                    v = api_tpl_dict.get(k, "")
                    if v:
                        v = self._add_tpl_handler(k, v, nosnow)
                        if subdir:
                            v = v.replace(
                                "from app.services.tpl import", f"from app.services.{subdir}.tpl import"
                            ).replace("from app.models.tpl import", f"from app.models.{subdir}.tpl import")
                        v = (
                            v.replace("tpls", names)
                            .replace("tpl", name)
                            .replace("Tpl", "".join(word.capitalize() or "_" for word in name.split("_")))
                        )
                    f.write(v)

    @staticmethod
    def _add_tpl_handler(k, v, nosnow: bool):
        if nosnow:
            if "models" in k:
                v = v.replace("import gen_snow_id", "import gen_uuid_hex").replace(
                    "id = mapped_column(BigInteger, primary_key=True, default=gen_snow_id",
                    "id = mapped_column(String(32), primary_key=True, default=gen_uuid_hex",
                )
            elif "services" in k:
                v = re.sub(r'^\s*converters={"id": str},*$\n?', "", v, flags=re.MULTILINE)
                v = v.replace('str(result.data["id"])', 'result.data["id"]').replace(
                    'where={"id": int(tpl_id)},', 'where={"id": tpl_id},'
                )
        return v

    @staticmethod
    def _add_celery_handler(names: list):
        work_dir = Path.cwd()
        with open(here.joinpath("_project_tpl.json"), "r", encoding="utf-8") as f:
            project_tpl = json.loads(f.read())
        sys.stdout.write("Adding celery:\n")
        f = False
        for name in names:
            if name == "celery":
                sys.stdout.write(f"[celery] Cannot use reserved name '{name}'\n")
                continue
            f = True
            celery_dir = work_dir.joinpath(name)
            if celery_dir.is_dir():
                sys.stdout.write(f"[celery] Existed {name}\n")
                continue
            sys.stdout.write(f"[celery] Writing {name}\n")
            celery_dir.mkdir(parents=True, exist_ok=True)
            for k, v in project_tpl.items():
                if k.startswith("app_celery/"):
                    tplpath = celery_dir.joinpath(k.replace("app_celery/", ""))
                    tplpath.parent.mkdir(parents=True, exist_ok=True)
                    with open(tplpath, "w", encoding="utf-8") as f:
                        v = v.replace("app_celery", name).replace("app-celery", name.replace("_", "-"))
                        f.write(v)
        if f:
            for ext in ["runcbeat.py", "runcworker.py", "app/api/default/aping.py"]:
                if ext == "app/api/default/aping.py" and not (work_dir / "app/api/default").is_dir():
                    continue
                path = work_dir / ext
                if path.is_file():
                    sys.stdout.write(f"[celery] Existed {ext}\n")
                else:
                    sys.stdout.write(f"[celery] Writing {ext}\n")
                    with open(path, "w", encoding="utf-8") as f:
                        v = project_tpl[ext]
                        v = v.replace("app_celery", names[0])
                        f.write(v)


if __name__ == "__main__":
    main()
