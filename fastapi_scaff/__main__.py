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
        "-e",
        "--edition",
        default="standard",
        choices=["standard", "light", "tiny", "single"],
        metavar="",
        help="`new`时可指定项目结构版本(默认标准版)")
    parser.add_argument(
        "-d",
        "--db",
        default="sqlite",
        choices=["sqlite", "mysql", "postgresql"],
        metavar="",
        help="`new`时可指定项目数据库(默认sqlite)")
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
        "-t",
        "--target",
        default="asm",
        choices=["a", "as", "asm"],
        metavar="",
        help="`add`时可指定目标(默认asm)")
    parser.add_argument(
        "--celery",
        action='store_true',
        help="`new`|`add`时可指定是否集成celery(默认不集成)")
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
                k, v = self._replace_handler(k, v)
            if not k:
                continue
            tplpath = name.joinpath(k)
            tplpath.parent.mkdir(parents=True, exist_ok=True)
            if base64_flag:
                with open(tplpath, "wb") as f:
                    f.write(base64.b64decode(v))
                    continue
            with open(tplpath, "w", encoding="utf-8") as f:
                f.write(v)
        sys.stdout.write("Done. Now run:\n"
                         f"> 1. cd {name}\n"
                         f"> 2. modify config{', eg: db' if self.args.edition != 'single' else ''}\n"
                         f"> 3. pip install -r requirements.txt\n"
                         f"> 4. python runserver.py\n"
                         f"----- More see README.md -----\n")

    def _replace_handler(self, k: str, v: str):
        if not self.args.celery:
            if k.startswith("app_celery/") or k in [
                "app/api/default/aping.py",
                "runcbeat.py",
                "runcworker.py",
            ]:
                return None, None
        if "tiny" in k and self.args.edition != "tiny":
            return None, None
        elif "single" in k and self.args.edition != "single":
            return None, None
        if self.args.edition == "standard":
            k, v = self._replace_by_standard(k, v)
        elif self.args.edition == "light":
            k, v = self._replace_by_light(k, v)
        elif self.args.edition == "tiny":
            k, v = self._replace_by_tiny(k, v)
        elif self.args.edition == "single":
            k, v = self._replace_by_single(k, v)
        if not k:
            return k, v
        if k == "app/api/status.py":
            if self.args.edition in ["light", "tiny"]:
                v = re.sub(r'^\s*USER_OR_PASSWORD_ERROR.*$\n?', '', v, flags=re.MULTILINE)
        elif k == "config/.env":
            if self.args.edition != "standard":
                v = re.sub(r'^\s*# 雪花算法数据中心id.*$\n^\s*snow_datacenter_id=.*$\n?', '', v, flags=re.MULTILINE)
        elif env := re.search(r"config/app_(.*).yaml$", k):
            if not self.args.celery:
                v = re.sub(r'^\s*# #\s*\n(?:^\s*celery_.*$\n?)+', '', v, flags=re.MULTILINE)
            if self.args.edition != "standard":
                v = re.sub(r'^\s*redis_.*$\n?', '', v, flags=re.MULTILINE)
            if self.args.edition == "single":
                v = re.sub(r'^\s*# #\s*\n(?:^\s*db_.*$\n?)+', '', v, flags=re.MULTILINE)
            else:
                _env = env.group(1)
                if self.args.db == "mysql":
                    v = v.replace(f"""db_drivername: sqlite
db_async_drivername: sqlite+aiosqlite
db_database: app_{_env}.sqlite
db_username:
db_password:
db_host:
db_port:
db_charset:""", """db_drivername: mysql+pymysql
db_async_drivername: mysql+aiomysql
db_database: <database>
db_username: <username>
db_password: <password>
db_host: <host>
db_port: <port>
db_charset: utf8mb4""")
                elif self.args.db == "postgresql":
                    v = v.replace(f"""db_drivername: sqlite
db_async_drivername: sqlite+aiosqlite
db_database: app_{_env}.sqlite
db_username:
db_password:
db_host:
db_port:
db_charset:""", """db_drivername: postgresql+psycopg2
db_async_drivername: postgresql+asyncpg
db_database: <database>
db_username: <username>
db_password: <password>
db_host: <host>
db_port: <port>
db_charset:""")
        elif k == "config/nginx.conf":
            v = v.replace("server backend:", f"server {self.args.name.replace('_', '-')}-prod_backend:")
        elif k.startswith((
                "build.sh",
                "docker-compose.",
        )):
            v = v.replace("fastapi-scaff", self.args.name.replace("_", "-"))
        elif k == "README.md":
            v = v.replace(f"# {prog}", f"# {prog} ( => yourProj)")
        elif k == "requirements.txt":
            if not self.args.celery:
                v = re.sub(r'^celery==.*$\n?', '', v, flags=re.MULTILINE)
                if self.args.edition != "standard":
                    v = re.sub(r'^redis==.*$\n?', '', v, flags=re.MULTILINE)
            if self.args.edition == "single":
                v = re.sub(r'^(PyJWT==|bcrypt==|SQLAlchemy==|alembic==|aiosqlite==).*$\n?', '', v, flags=re.MULTILINE)
            else:
                if self.args.db != "sqlite":
                    _default = "aiosqlite=="
                    _user = {
                        "sqlite": [
                            "aiosqlite==0.21.0",
                        ],
                        "mysql": [
                            "PyMySQL==1.1.2",
                            "aiomysql==0.3.2",
                        ],
                        "postgresql": [
                            "psycopg2-binary==2.9.11",
                            "asyncpg==0.31.0",
                        ],
                    }.get(self.args.db)
                    v = re.sub(rf'^{_default}.*$\n?', '\n'.join(_user) + '\n', v, flags=re.MULTILINE)
                if self.args.edition == "tiny":
                    v = re.sub(r'^alembic==.*$\n?', '', v, flags=re.MULTILINE)
        return k, v

    @staticmethod
    def _replace_by_standard(k, v):
        return k, v

    @staticmethod
    def _replace_by_light(k, v):
        if re.match(r"^({filter_k})".format(filter_k="|".join([
            "app/api/v1/user.py",
            "app/initializer/_redis.py",
            "app/initializer/_snow.py",
            "app/models/",
            "app/repositories/",
            "app/schemas/",
            "app/services/user.py",
            "docs/",
            "tests/",
        ])), k) is not None:
            return None, None
        elif k == "app/initializer/__init__.py":
            v = v.replace("""from toollib.guid import SnowFlake
from toollib.rediscli import RedisCli
""", "").replace("""from app.initializer._redis import init_redis_cli
from app.initializer._snow import init_snow_cli
""", "").replace("""'redis_cli',
        'snow_cli',
        """, "").replace("""@cached_property
    def redis_cli(self) -> RedisCli:
        return init_redis_cli(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            password=self.config.redis_password,
            max_connections=self.config.redis_max_connections,
        )

    @cached_property
    def snow_cli(self) -> SnowFlake:
        return init_snow_cli(
            redis_cli=self.redis_cli,
            datacenter_id=self.config.snow_datacenter_id,
        )

    """, "")
        elif k == "app/initializer/_conf.py":
            v = v.replace("""snow_datacenter_id: int = None
    """, "")
            v = re.sub(r'^\s*redis_.*$\n?', '', v, flags=re.MULTILINE)
        elif k == "app/initializer/_db.py":
            v = v.replace(
                """_MODELS_MOD_DIR = APP_DIR.joinpath("models")""",
                """_MODELS_MOD_DIR = APP_DIR.joinpath("services")""").replace(
                """_MODELS_MOD_BASE = "app.models\"""",
                """_MODELS_MOD_BASE = "app.services\"""")
        elif k == "app/services/__init__.py":
            v = v.replace("""\"\"\"
业务逻辑
\"\"\"""", """\"\"\"
业务逻辑
\"\"\"
from sqlalchemy.orm import DeclarativeBase


class DeclBase(DeclarativeBase):
    pass


# DeclBase 使用示例（官方文档：https://docs.sqlalchemy.org/en/latest/orm/quickstart.html#declare-models）
\"\"\"
from sqlalchemy import Column, String

from app.services import DeclBase


class User(DeclBase):
    __tablename__ = "user"

    id = Column(String(20), primary_key=True, comment="主键")
    name = Column(String(50), nullable=False, comment="名称")
\"\"\"""")
        return k, v

    @staticmethod
    def _replace_by_tiny(k, v):
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
            "runmigration.py",
        ])), k) is not None:
            return None, None
        elif k.startswith("tiny/"):
            k = k.replace("tiny/", "")
        elif k == "app/api/responses.py":
            v = v.replace("""from app.initializer.context import request_id_var""",
                          """from app.initializer import request_id_var""")
        return k, v

    @staticmethod
    def _replace_by_single(k, v):
        if re.match(r"^({filter_k})".format(filter_k="|".join([
            "app/",
            "docs/",
            "tests/",
            "runmigration.py",
        ])), k) is not None:
            return None, None
        elif k.startswith("single/"):
            k = k.replace("single/", "")
        return k, v

    def add(self):
        if self.args.celery:
            return self._add_celery_handler(self.args.name.split(","))
        vn = self.args.vn
        subdir = self.args.subdir
        target = self.args.target

        work_dir = Path.cwd()
        with open(here.joinpath("_api_tpl.json"), "r", encoding="utf-8") as f:
            api_tpl_dict = json.loads(f.read())
        if target != "a":
            if not any([
                work_dir.joinpath("app/schemas").is_dir(),
                work_dir.joinpath("app/models").is_dir(),
            ]):
                target = "light"
                if not work_dir.joinpath("app/services").is_dir():
                    target = "tiny"
        if target in ["a", "tiny"]:
            tpl_mods = [
                "app/api",
            ]
        elif target == "light":
            tpl_mods = [
                "app/api",
                "app/services",
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
                sys.stderr.write(f"[error] not exists: {mod.replace('/', os.sep)}")
                sys.exit(1)
        for name in self.args.name.split(","):
            sys.stdout.write(f"Adding api:\n")
            flags = {
                # - 键：目标是否存在: 0-no，1-yes
                # - 值：创建是否关联: 0-no，1-yes
                #   - 创建a时，se取反
                #   - 创建se时，sc取反
                #   - 创建sc时，全为1
                #   - 创建m时，全为1
                #   - 创建r时，m取反
                #   - light:
                #       - 创建a时，se取反
                #       - 创建se时，a取反
                # a|tiny (a)
                "0": [1],
                "1": [1],
                # as (a, se, sc)
                "000": [1, 1, 1],
                "001": [1, 0, 1],
                "010": [0, 1, 1],
                "011": [0, 0, 1],
                "100": [1, 1, 1],
                "101": [1, 0, 1],
                "110": [0, 1, 1],
                "111": [0, 0, 1],
                # asm (a, se, sc, m(&r))
                "00000": [1, 1, 1, 1, 1],
                "00001": [1, 1, 1, 1, 1],
                "00010": [1, 1, 1, 1, 0],
                "00011": [1, 1, 1, 1, 0],
                "00100": [1, 0, 1, 1, 1],
                "00101": [1, 0, 1, 1, 1],
                "00110": [1, 0, 1, 1, 0],
                "00111": [1, 0, 1, 1, 0],
                "01000": [0, 1, 1, 1, 1],
                "01001": [0, 1, 1, 1, 1],
                "01010": [0, 1, 1, 1, 0],
                "01011": [0, 1, 1, 1, 0],
                "01100": [0, 0, 1, 1, 1],
                "01101": [0, 0, 1, 1, 1],
                "01110": [0, 0, 1, 1, 0],
                "01111": [0, 0, 1, 1, 0],
                "10000": [1, 1, 1, 1, 1],
                "10001": [1, 1, 1, 1, 1],
                "10010": [1, 1, 1, 1, 0],
                "10011": [1, 1, 1, 1, 0],
                "10100": [1, 0, 1, 1, 1],
                "10101": [1, 0, 1, 1, 1],
                "10110": [1, 0, 1, 1, 0],
                "10111": [1, 0, 1, 1, 0],
                "11000": [0, 1, 1, 1, 1],
                "11001": [0, 1, 1, 1, 1],
                "11010": [0, 1, 1, 1, 0],
                "11011": [0, 1, 1, 1, 0],
                "11100": [0, 0, 1, 1, 1],
                "11101": [0, 0, 1, 1, 1],
                "11110": [0, 0, 1, 1, 0],
                "11111": [0, 0, 1, 1, 0],
                # light (a, se)
                "00": [1, 1],
                "01": [0, 1],
                "10": [1, 0],
                "11": [0, 0],
            }
            e_flag = [
                1 if (Path(work_dir, mod, vn if mod.endswith("api") else "", subdir, f"{name}.py")).is_file() else 0
                for mod in tpl_mods
            ]
            p_flag = flags["".join(map(str, e_flag))]
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
                                sys.stderr.write(f"[error] create {curr_mod_dir_rel} failed: {e}\n")
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
                curr_mod_file_rel = curr_mod_file.relative_to(work_dir)
                if e_flag[i]:
                    sys.stdout.write(f"[{name}] Existed {curr_mod_file_rel}\n")
                else:
                    with open(curr_mod_file, "w", encoding="utf-8") as f:
                        sys.stdout.write(f"[{name}] Writing {curr_mod_file_rel}\n")
                        prefix = f"{target}_" if p_flag[i] else "only_"
                        k = prefix + mod.replace("/", "_") + ".py"
                        v = api_tpl_dict.get(k, "")
                        if v:
                            if subdir:
                                v = v.replace(
                                    "from app.schemas.tpl import (", f"from app.schemas.{subdir}.tpl import ("
                                ).replace(
                                    "from app.services.tpl import (", f"from app.services.{subdir}.tpl import ("
                                ).replace(
                                    "from app.models.tpl import (", f"from app.models.{subdir}.tpl import ("
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
                sys.stdout.write(f"[{name}] Can't be `celery`\n")
                continue
            f = True
            celery_dir = work_dir.joinpath(name)
            if celery_dir.is_dir():
                sys.stdout.write(f"[{name}] Existed\n")
                continue
            sys.stdout.write(f"[{name}] Writing\n")
            celery_dir.mkdir(parents=True, exist_ok=True)
            for k, v in project_tpl.items():
                if k.startswith("app_celery/"):
                    tplpath = celery_dir.joinpath(k.replace("app_celery/", ""))
                    tplpath.parent.mkdir(parents=True, exist_ok=True)
                    with open(tplpath, "w", encoding="utf-8") as f:
                        v = v.replace("app_celery", name).replace("app-celery", name.replace("_", "-"))
                        f.write(v)
        if not f: return
        for ext in ["runcbeat.py", "runcworker.py", "app/api/default/aping.py"]:
            if ext == "app/api/default/aping.py" and not (work_dir / "app/api/default").is_dir():
                continue
            path = work_dir / ext
            if path.is_file():
                sys.stdout.write(f"[{ext}] Existed\n")
            else:
                sys.stdout.write(f"[{ext}] Writing\n")
                with open(path, "w", encoding="utf-8") as f:
                    v = project_tpl[ext]
                    v = v.replace("app_celery", names[0])
                    f.write(v)


if __name__ == "__main__":
    main()
