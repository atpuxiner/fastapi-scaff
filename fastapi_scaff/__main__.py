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

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

here = Path(__file__).absolute().parent
prog = "fastapi-scaff"


def main():
    parser = argparse.ArgumentParser(
        prog=prog,
        description="fastapi脚手架，一键生成项目或api，让开发变得更简单",
        epilog="examples: \n"
               "  `new`: %(prog)s new <myproj>\n"
               "  `add`: %(prog)s add <myapi>\n"
               "",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}")
    parser.add_argument(
        "command",
        choices=["new", "add"],
        help="创建项目或添加api")
    parser.add_argument(
        "name",
        type=str,
        help="项目或api名称(多个api可逗号分隔)")
    parser.add_argument(
        "-t",
        "--template",
        default="standard",
        choices=["standard", "light", "tiny", "single"],
        metavar="",
        help="`new`时可指定项目模板(默认标准版)")
    parser.add_argument(
        "-d",
        "--db",
        default="sqlite",
        choices=["sqlite", "mysql", "postgresql", "no"],
        metavar="",
        help="`new`时可指定项目数据库(默认sqlite,no表不集成)")
    parser.add_argument(
        "-v",
        "--vn",
        default="v1",
        type=str,
        metavar="",
        help="`add`时可指定版本(默认v1)")
    parser.add_argument(
        "-s",
        "--subdir",
        default="",
        type=str,
        metavar="",
        help="`add`时可指定子目录(默认空)")
    parser.add_argument(
        "--celery",
        action='store_true',
        help="`new`|`add`时可指定celery(默认不集成)")
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
            pattern = r"^[A-Za-z][A-Za-z0-9_-]{0,64}$"
            if not re.search(pattern, args.name):
                sys.stderr.write(f"{prog}: '{args.name}' only support regex: {pattern}\n")
                sys.exit(1)
        else:
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
            if args.subdir:
                if not re.search(pattern, args.subdir):
                    sys.stderr.write(f"{prog}: '{args.subdir}' only support regex: {pattern}\n")
                    sys.exit(1)
        self.args = args

    def new(self):
        sys.stdout.write("Starting new project...\n")
        name = Path(self.args.name)
        if name.is_dir() and any(name.iterdir()):
            sys.stderr.write(f"{prog}: '{name}' exists\n")
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
        sys.stdout.write("Done. Now run:\n"
                         f"> 1. cd {name}\n"
                         f"> 2. modify config{'' if (self.args.template == 'single' or self.args.db == 'no') else ', eg: db'}\n"
                         f"> 3. pip install -r requirements.txt\n"
                         f"> 4. python runserver.py\n"
                         f"----- More see README.md -----\n")

    def _tpl_handler(self, k: str, v: str):
        if not self.args.celery:
            if k in [
                "app/api/default/aping.py",
                "runcbeat.py",
                "runcworker.py",
            ]:
                k, v = None, None
            elif k.startswith("app_celery/"):
                k, v = None, None
            elif re.search(r"config/app_(.*).yaml$", k):
                v = re.sub(r'^\s*# #\s*\n(?:^\s*celery_.*$\n?)+', '', v, flags=re.MULTILINE)
            elif k == "requirements.txt":
                v = re.sub(r'^celery==.*$\n?', '', v, flags=re.MULTILINE)
                if self.args.template != "standard":
                    v = re.sub(r'^redis==.*$\n?', '', v, flags=re.MULTILINE)
        if k:
            if self.args.template == "light":
                k, v = self._tpl_handle_by_light(k, v)
            elif self.args.template == "tiny":
                k, v = self._tpl_handle_by_tiny(k, v)
            elif self.args.template == "single":
                k, v = self._tpl_handle_by_single(k, v)
            else:
                k, v = self._tpl_handle_by_standard(k, v)
            if k and self.args.db == "no":
                k, v = self._tpl_handle_by_db_no(k, v)
        if not k:
            return k, v
        if k == "config/nginx.conf":
            v = v.replace("server backend:", f"server {self.args.name.replace('_', '-')}-prod_backend:")
        elif k.startswith((
                "build.sh",
                "docker-compose.",
        )):
            v = v.replace("fastapi-scaff", self.args.name.replace("_", "-"))
        elif k == "README.md":
            v = v.replace(f"# {prog}", f"# {prog} ( => yourProj)")
        return k, v

    @staticmethod
    def _tpl_handle_by_standard(k, v):
        if k.startswith((
                "tiny/",
                "single/",
        )):
            return None, None
        return k, v

    def _tpl_handle_by_light(self, k, v):
        if re.match(r"^({filter_k})".format(filter_k="|".join([
            "app/api/v1/user.py",
            "app/initializer/_redis.py",
            "app/initializer/_snow.py",
            "app/models/",
            "app/repositories/",
            "app/schemas/user.py",
            "app/services/user.py",
            "docs/",
            "tests/",
            "tiny/",
            "single/",
        ])), k) is not None:
            return None, None
        elif k == "app/api/status.py":
            v = re.sub(r'^\s*USER_OR_PASSWORD_ERROR.*$\n?', '', v, flags=re.MULTILINE)
        elif k == "app/initializer/__init__.py":
            v = re.sub(r'^\s*from\s+.*?(redis|snow|Snow).*?$\n?', '', v, flags=re.MULTILINE)
            v = re.sub(r'^\s*(?:#\s*)?"(redis_cli|snow_cli)",?\s*\n', '', v, flags=re.MULTILINE)
            v = re.sub(
                rf'^(\s*@[^\n]*\n)*\s*def\s+(redis_cli|snow_cli)\s*\([^)]*\)[^:]*:\n(?:\s+.*\n)*?(?=\n+\s+\S+|\Z)',
                '', v, flags=re.MULTILINE
            )
        elif k == "app/initializer/_conf.py":
            v = re.sub(r'^\s*(redis_|snow_).*$\n?', '', v, flags=re.MULTILINE)
        elif k == "app/initializer/_db.py":
            v = v.replace(
                """_MODELS_MOD_DIR = APP_DIR.joinpath("models")""",
                """_MODELS_MOD_DIR = APP_DIR.joinpath("schemas")""").replace(
                """_MODELS_MOD_BASE = "app.models\"""",
                """_MODELS_MOD_BASE = "app.schemas\"""")
        elif k == "app/schemas/__init__.py":
            v = '"""\n数据结构\n"""\nfrom sqlalchemy.orm import DeclarativeBase\n\n\nclass DeclBase(DeclarativeBase):\n    pass\n\n\n# DeclBase 使用示例（官方文档：https://docs.sqlalchemy.org/en/latest/orm/quickstart.html#declare-models）\n"""\nfrom sqlalchemy import Column, String\n\nfrom app.services import DeclBase\n\n\nclass User(DeclBase):\n    __tablename__ = "user"\n\n    id = Column(String(20), primary_key=True, comment="主键")\n    name = Column(String(50), nullable=False, comment="名称")\n"""\n\n\ndef filter_fields(\n        model,\n        exclude: list = None,\n):\n    if exclude:\n        return list(set(model.model_fields.keys()) - set(exclude))\n    return list(model.model_fields.keys())\n'
        elif k == "config/.env":
            v = re.sub(r'(?:^[ \t]*#[^\n]*\n)*^[ \t]*snow_[^\n]*\n?', '', v, flags=re.MULTILINE)
        elif env := re.search(r"config/app_(.*).yaml$", k):
            v = re.sub(r'^\s*redis_.*$\n?', '', v, flags=re.MULTILINE)
            ov = f'db_drivername: sqlite\ndb_async_drivername: sqlite+aiosqlite\ndb_database: app_{env.group(1)}.sqlite\ndb_username:\ndb_password:\ndb_host:\ndb_port:\ndb_charset:'
            if self.args.db == "mysql":
                nv = 'db_drivername: mysql+pymysql\ndb_async_drivername: mysql+aiomysql\ndb_database: <database>\ndb_username: <username>\ndb_password: <password>\ndb_host: <host>\ndb_port: <port>\ndb_charset: utf8mb4'
                v = v.replace(ov, nv)
            elif self.args.db == "postgresql":
                nv = 'db_drivername: postgresql+psycopg2\ndb_async_drivername: postgresql+asyncpg\ndb_database: <database>\ndb_username: <username>\ndb_password: <password>\ndb_host: <host>\ndb_port: <port>\ndb_charset:'
                v = v.replace(ov, nv)
        elif k == "requirements.txt":
            if self.args.db == "mysql":
                mysql = [
                    "PyMySQL==1.1.2",
                    "aiomysql==0.3.2",
                ]
                v = re.sub(rf'^aiosqlite==.*$\n?', '\n'.join(mysql) + '\n', v, flags=re.MULTILINE)
            elif self.args.db == "postgresql":
                postgresql = [
                    "psycopg2-binary==2.9.11",
                    "asyncpg==0.31.0",
                ]
                v = re.sub(rf'^aiosqlite==.*$\n?', '\n'.join(postgresql) + '\n', v, flags=re.MULTILINE)
        return k, v

    def _tpl_handle_by_tiny(self, k, v):
        if re.match(r"^({filter_k})".format(filter_k="|".join([
            "app/api/v1/user.py",
            "app/initializer/",
            "app/middleware/",
            "app/migrations/",
            "app/models/",
            "app/repositories/",
            "app/schemas/",
            "app/services/",
            "docs/",
            "tests/",
            "single/",
            "runmigration.py",
        ])), k) is not None:
            return None, None
        elif k.startswith("tiny/"):
            k = k.replace("tiny/", "")
        elif k == "app/api/responses.py":
            v = v.replace(
                """from app.initializer.context import request_id_var""",
                """from app.initializer import request_id_var"""
            )
        elif k == "app/api/status.py":
            v = re.sub(r'^\s*USER_OR_PASSWORD_ERROR.*$\n?', '', v, flags=re.MULTILINE)
        elif k == "config/.env":
            v = re.sub(r'(?:^[ \t]*#[^\n]*\n)*^[ \t]*snow_[^\n]*\n?', '', v, flags=re.MULTILINE)
        elif env := re.search(r"config/app_(.*).yaml$", k):
            v = re.sub(r'^\s*redis_.*$\n?', '', v, flags=re.MULTILINE)
            ov = f'db_drivername: sqlite\ndb_async_drivername: sqlite+aiosqlite\ndb_database: app_{env.group(1)}.sqlite\ndb_username:\ndb_password:\ndb_host:\ndb_port:\ndb_charset:'
            if self.args.db == "mysql":
                nv = 'db_drivername: mysql+pymysql\ndb_async_drivername: mysql+aiomysql\ndb_database: <database>\ndb_username: <username>\ndb_password: <password>\ndb_host: <host>\ndb_port: <port>\ndb_charset: utf8mb4'
                v = v.replace(ov, nv)
            elif self.args.db == "postgresql":
                nv = 'db_drivername: postgresql+psycopg2\ndb_async_drivername: postgresql+asyncpg\ndb_database: <database>\ndb_username: <username>\ndb_password: <password>\ndb_host: <host>\ndb_port: <port>\ndb_charset:'
                v = v.replace(ov, nv)
        elif k == "requirements.txt":
            v = re.sub(r'^alembic==.*$\n?', '', v, flags=re.MULTILINE)
            if self.args.db == "mysql":
                mysql = [
                    "PyMySQL==1.1.2",
                    "aiomysql==0.3.2",
                ]
                v = re.sub(rf'^aiosqlite==.*$\n?', '\n'.join(mysql) + '\n', v, flags=re.MULTILINE)
            elif self.args.db == "postgresql":
                postgresql = [
                    "psycopg2-binary==2.9.11",
                    "asyncpg==0.31.0",
                ]
                v = re.sub(rf'^aiosqlite==.*$\n?', '\n'.join(postgresql) + '\n', v, flags=re.MULTILINE)
        return k, v

    def _tpl_handle_by_single(self, k, v):
        if re.match(r"^({filter_k})".format(filter_k="|".join([
            "app/",
            "docs/",
            "tests/",
            "tiny/",
            "runmigration.py",
        ])), k) is not None:
            return None, None
        elif k.startswith("single/"):
            k = k.replace("single/", "")
        elif k == "config/.env":
            v = re.sub(r'(?:^[ \t]*#[^\n]*\n)*^[ \t]*snow_[^\n]*\n?', '', v, flags=re.MULTILINE)
        elif re.search(r"config/app_(.*).yaml$", k):
            v = re.sub(r'^\s*redis_.*$\n?', '', v, flags=re.MULTILINE)
            v = re.sub(r'^\s*# #\s*\n(?:^\s*db_.*$\n?)+', '', v, flags=re.MULTILINE)
        elif k == "requirements.txt":
            v = re.sub(r'^(PyJWT==|bcrypt==|SQLAlchemy==|alembic==|aiosqlite==).*$\n?', '', v, flags=re.MULTILINE)
        return k, v

    @staticmethod
    def _tpl_handle_by_db_no(k, v):
        if k in [
            "app/initializer/_db.py",
            "app/initializer/_snow.py",
            "app/utils/db_util.py",
            "app/utils/jwt_util.py",
            "runmigration.py",
        ]:
            return None, None
        elif k.startswith("app/migrations/"):
            return None, None
        elif k.endswith("user.py"):
            return None, None
        elif k == "app/api/dependencies.py":
            v = 'from fastapi import Security\nfrom fastapi.security import APIKeyHeader\n\nfrom app.api.exceptions import CustomException\nfrom app.api.status import Status\nfrom app.initializer import g\n\n# ======= api key =======\n\n_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)\n\n\nasync def get_current_api_key(api_key: str | None = Security(_API_KEY_HEADER)):\n    if not api_key:\n        raise CustomException(status=Status.UNAUTHORIZED_ERROR, msg="API key is required")\n    if api_key not in g.config.api_keys:\n        raise CustomException(status=Status.UNAUTHORIZED_ERROR, msg="Invalid API key")\n    return api_key\n'
        elif k == "app/initializer/__init__.py":
            v = re.sub(r'^from.*(sqlalchemy|Snow|_db|_snow).*$\n?', '', v, flags=re.MULTILINE)
            v = re.sub(r'^\s*(?:#\s*)?"(db_session|db_async_session|snow_cli)",?\s*\n', '', v, flags=re.MULTILINE)
            v = re.sub(
                rf'^(\s*@[^\n]*\n)*\s*def\s+(db_session|db_async_session|snow_cli)\s*\([^)]*\)[^:]*:\n(?:\s+.*\n)*?(?=\n+\s+\S+|\Z)',
                '', v, flags=re.MULTILINE
            )
        elif k == "app/initializer/_conf.py":
            v = re.sub(r'^\s*(db_|snow_).*$\n?', '', v, flags=re.MULTILINE)
            v = re.sub(r'^\s*# #[ \t]*\n(?=\s*\n)', '', v, flags=re.MULTILINE)
        elif k == "app/initializer.py":
            v = re.sub(r'^from.*sqlalchemy.*$\n?', '', v, flags=re.MULTILINE)
            v = re.sub(r'^\s*db_.*$\n?', '', v, flags=re.MULTILINE)
            v = re.sub(
                rf'^(\s*@[^\n]*\n)*\s*def\s+(init_db_session|init_db_async_session|make_db_url|db_session|db_async_session)\s*\([^)]*\)[^:]*:\n(?:\s+.*\n)*?(?=\n+\s+\S+|\Z)',
                '', v, flags=re.MULTILINE
            )
            v = re.sub(r'^\s*(?:#\s*)?"(db_session|db_async_session)",?\s*\n', '', v, flags=re.MULTILINE)
            v = re.sub(r'^\s*# #[ \t]*\n(?=\s*\n)', '', v, flags=re.MULTILINE)
        elif k == "app/models/__init__.py":
            v = '"""\n数据模型\n"""\n'
        elif k == "app/schemas/__init__.py":
            v = '"""\n数据结构\n"""\n'
        elif k == "app/services/__init__.py":
            v = '"""\n业务逻辑\n"""\n'
        elif k == "config/.env":
            v = re.sub(r'(?:^[ \t]*#[^\n]*\n)*^[ \t]*snow_[^\n]*\n?', '', v, flags=re.MULTILINE)
        elif re.search(r"config/app_(.*).yaml$", k):
            v = re.sub(r'^\s*# #\s*\n(?:^\s*db_.*$\n?)+', '', v, flags=re.MULTILINE)
        elif k == "requirements.txt":
            v = re.sub(r'^(PyJWT==|bcrypt==|SQLAlchemy==|alembic==|aiosqlite==).*$\n?', '', v, flags=re.MULTILINE)
        return k, v

    def add(self):
        if self.args.celery:
            return self._add_celery_handler(self.args.name.split(","))
        vn = self.args.vn
        subdir = self.args.subdir

        work_dir = Path.cwd()
        with open(here.joinpath("_api_tpl.json"), "r", encoding="utf-8") as f:
            api_tpl_dict = json.loads(f.read())

        target = "asm"
        has_decl_base = False
        if not work_dir.joinpath("app/models").is_dir():
            target = "as"
            if not work_dir.joinpath("app/services").is_dir():
                target = "a"
        else:
            decl_file = work_dir.joinpath("app/models/__init__.py")
            if decl_file.is_file():
                if re.search(
                        r"^\s*class\s+DeclBase\s*\(\s*DeclarativeBase\s*\)\s*:",
                        decl_file.read_text("utf-8"),
                        re.MULTILINE
                ):
                    has_decl_base = True
        if target == "a":
            tpl_mods = [
                "app/api",
            ]
        elif target == "as":
            tpl_mods = [
                "app/api",
                "app/services",
                "app/schemas",
            ]
        else:
            tpl_mods = [
                "app/api",
                "app/services",
                "app/schemas",
                "app/models",
                "app/repositories",
            ]
        for mod in tpl_mods:
            if not work_dir.joinpath(mod).is_dir():
                sys.stderr.write(f"[error] Not exists: {mod.replace('/', os.sep)}\n")
                sys.exit(1)
        for name in self.args.name.split(","):
            sys.stdout.write(f"Adding api:\n")
            existed_file = None
            for mod in tpl_mods:
                if mod == "app/api":
                    mod = f"{mod}/{vn}"
                if subdir:
                    mod = mod + os.sep + subdir
                curr_mod_file = work_dir.joinpath(mod, name + ".py")
                if curr_mod_file.is_file():
                    existed_file = curr_mod_file
                    break
            if existed_file:
                sys.stderr.write(
                    f"[{name}] Existed {existed_file.relative_to(work_dir)}. Operation cancelled, please handle manually.\n")
                continue
            for i, mod in enumerate(tpl_mods):
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
                                    f.write("""\"\"\"\napi-{vn}\n\"\"\"\n\n_prefix = "/api/{vn}"\n""".format(
                                        vn=vn,
                                    ))
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
                            f.write("""\"\"\"\n{subdir}\n\"\"\"\n\n_prefix = "/{subdir}"\n""".format(
                                subdir=subdir,
                            ))
                # file
                curr_mod_file = curr_mod_dir.joinpath(name + ".py")
                with open(curr_mod_file, "w", encoding="utf-8") as f:
                    sys.stdout.write(f"[{name}] Writing {curr_mod_file.relative_to(work_dir)}\n")
                    if not has_decl_base:
                        api_tpl_dict[
                            "as_app_schemas.py"] = 'from pydantic import BaseModel, Field\n\n\nclass TplDetail(BaseModel):\n    id: str = Field(...)\n    # #\n    name: str = None\n'
                        api_tpl_dict[
                            "asm_app_schemas.py"] = 'from pydantic import BaseModel, Field\n\n\nclass TplDetail(BaseModel):\n    id: str = Field(...)\n    # #\n    name: str = None\n'
                        api_tpl_dict["asm_app_models.py"] = '\n\nclass Tpl:\n    __tablename__ = "tpl"\n'
                        api_tpl_dict[
                            "asm_app_repositories.py"] = '\n\nclass TplRepo:\n\n    def __init__(self, session, model):\n        self.session = session\n        self.model = model\n\n    async def get_user_detail(self):\n        pass\n'
                    k = f"{target}_{mod.replace('/', '_')}.py"
                    v = api_tpl_dict.get(k, "")
                    if v:
                        if subdir:
                            v = v.replace(
                                "from app.services.tpl import", f"from app.services.{subdir}.tpl import"
                            ).replace(
                                "from app.schemas.tpl import", f"from app.schemas.{subdir}.tpl import"
                            ).replace(
                                "from app.models.tpl import", f"from app.models.{subdir}.tpl import"
                            ).replace(
                                "from app.repositories.tpl import", f"from app.schemas.{subdir}.tpl import"
                            )
                        v = v.replace(
                            "tpl", name).replace(
                            "Tpl", "".join([i[0].upper() + i[1:] if i else "_" for i in name.split("_")])
                        )
                    f.write(v)

    @staticmethod
    def _add_celery_handler(names: list):
        work_dir = Path.cwd()
        with open(here.joinpath("_project_tpl.json"), "r", encoding="utf-8") as f:
            project_tpl = json.loads(f.read())
        sys.stdout.write(f"Adding celery:\n")
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
