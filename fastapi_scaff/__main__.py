"""
@author axiner
@version v1.0.0
@created 2024/07/29 22:22
@abstract main
@description
@history
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from . import __version__

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
        "--light",
        action='store_true',
        help="`new`时可指定项目结构是否轻量版(默认标准版)")
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
        type=str,
        default="v1",
        metavar="",
        help="`add`时可指定版本(默认v1)")
    parser.add_argument(
        "-s",
        "--subdir",
        type=str,
        default="",
        metavar="",
        help="`add`时可指定子目录(默认空)")
    parser.add_argument(
        "-t",
        "--target",
        default="asm",
        choices=["a", "as", "asm"],
        metavar="",
        help="`add`时可指定目标(默认asm)")
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
            project = json.loads(f.read())
        for k, v in project.items():
            if self.args.light:
                k, v = self._light_handler(k, v)
                if not k:
                    continue
            tplpath = name.joinpath(k)
            tplpath.parent.mkdir(parents=True, exist_ok=True)
            with open(tplpath, "w+", encoding="utf-8") as f:
                # rpl
                if re.search(r"README\.md$", k):
                    v = v.replace(f"# {prog}", f"# {prog} ( => yourProj)")
                if re.search(r"requirements\.txt$", k):
                    _default = self._db_requirements_map("default")
                    _user = self._db_requirements_map(self.args.db) or _default
                    v = v.replace(
                        _default,
                        '\n'.join(_user)
                    )
                if _env := re.search(r"app_(.*?).yaml$", k):
                    _rpl_name = f"/app_{_env.group(1)}"
                    _default = self._db_yaml_map("default")
                    _user = self._db_yaml_map(self.args.db) or _default
                    v = v.replace(
                        _default["db_url"].replace("/app_dev", _rpl_name),
                        _user["db_url"].replace("/app_dev", _rpl_name)
                    ).replace(
                        _default["db_async_url"].replace("/app_dev", _rpl_name),
                        _user["db_async_url"].replace("/app_dev", _rpl_name)
                    )
                # < rpl
                f.write(v)
        sys.stdout.write("Done. Now run:\n"
                         f"> 1. cd {name}\n"
                         f"> 2. modify config, eg: db\n"
                         f"> 3. pip install -r requirements.txt\n"
                         f"> 4. python runserver.py\n"
                         f"----- More see README.md -----\n")

    @staticmethod
    def _light_handler(k: str, v: str):
        pat = r"^({filter_k})".format(filter_k="|".join([
            "app/api/default/aping.py",
            "app/api/v1/user.py",
            "app/initializer/_redis.py",
            "app/initializer/_snow.py",
            "app/models/",
            "app/schemas/",
            "app/services/user.py",
            "app_celery/",
            "deploy/",
            "docs/",
            "tests/",
            "runcbeat.py",
            "runcworker.py",
        ]))
        if re.match(pat, k) is not None:
            return None, None
        if k == "app/api/status.py":
            v = v.replace("""
    USER_OR_PASSWORD_ERROR = (10002, '用户名或密码错误')""", "")
        elif k == "app/initializer/__init__.py":
            v = v.replace("""
from toollib.guid import SnowFlake
from toollib.rediser import RedisClient""", "").replace("""
from app.initializer._redis import init_redis_client
from app.initializer._snow import init_snow_client""", "").replace("""
        'redis_client',
        'snow_client',""", "").replace("""
    @cached_property
    def redis_client(self) -> RedisClient:
        return init_redis_client(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            password=self.config.redis_password,
            max_connections=self.config.redis_max_connections,
        )

    @cached_property
    def snow_client(self) -> SnowFlake:
        return init_snow_client(
            redis_client=self.redis_client,
            datacenter_id=self.config.snow_datacenter_id,
        )
""", "")
        elif k == "app/initializer/_conf.py":
            v = v.replace("""redis_host: str = None
    redis_port: int = None
    redis_db: int = None
    redis_password: str = None
    redis_max_connections: int = None
    """, "")
        elif k == "app/initializer/_db.py":
            v = v.replace("""
_MODELS_MOD_DIR = APP_DIR.joinpath("models")
_MODELS_MOD_BASE = "app.models\"""", """
_MODELS_MOD_DIR = APP_DIR.joinpath("services")
_MODELS_MOD_BASE = "app.services\"""")
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
        elif k == "config/.env":
            v = v.replace("""# 雪花算法数据中心id（取值：0-31，在分布式部署时需确保每个节点的取值不同）
snow_datacenter_id=0
""", "")
        elif k.startswith("config/app_"):
            v = v.replace("""redis_host:
redis_port:
redis_db:
redis_password:
redis_max_connections:
""", "").replace("""# #
celery_broker_url: redis://:<password>@<host>:<port>/<db>
celery_backend_url: redis://:<password>@<host>:<port>/<db>
celery_timezone: Asia/Shanghai
celery_enable_utc: true
celery_task_serializer: json
celery_result_serializer: json
celery_accept_content: [ json ]
celery_task_ignore_result: false
celery_result_expire: 86400
celery_task_track_started: true
celery_worker_concurrency: 8
celery_worker_prefetch_multiplier: 2
celery_worker_max_tasks_per_child: 100
celery_broker_connection_retry_on_startup: true
celery_task_reject_on_worker_lost: true
""", "")
        elif k == "requirements.txt":
            v = v.replace("""
redis==6.4.0""", "").replace("""
celery==5.5.3""", "")
        return k, v

    @staticmethod
    def _db_requirements_map(name: str):
        return {
            "default": "aiosqlite==0.21.0",
            "sqlite": [
                "aiosqlite==0.21.0",
            ],
            "mysql": [
                "PyMySQL==1.1.2",
                "aiomysql==0.3.2",
            ],
            "postgresql": [
                "psycopg2-binary==2.9.11",
                "asyncpg==0.30.0",
            ],
        }.get(name)

    @staticmethod
    def _db_yaml_map(name: str):
        return {
            "default": {
                "db_url": "db_url: sqlite:///app_dev.sqlite",
                "db_async_url": "db_async_url: sqlite+aiosqlite:///app_dev.sqlite",
            },
            "sqlite": {
                "db_url": "db_url: sqlite:///app_dev.sqlite",
                "db_async_url": "db_async_url: sqlite+aiosqlite:///app_dev.sqlite",
            },
            "mysql": {
                "db_url": "db_url: mysql+pymysql://<username>:<password>@<host>:<port>/<database>?charset=utf8mb4",
                "db_async_url": "db_async_url: mysql+aiomysql://<username>:<password>@<host>:<port>/<database>?charset=utf8mb4",
            },
            "postgresql": {
                "db_url": "db_url: postgresql://<username>:<password>@<host>:<port>/<database>",
                "db_async_url": "db_async_url: postgresql+asyncpg://<username>:<password>@<host>:<port>/<database>",
            },
        }.get(name)

    def add(self):
        vn = self.args.vn
        subdir = self.args.subdir
        target = self.args.target

        work_dir = Path.cwd()
        with open(here.joinpath("_api_tpl.json"), "r", encoding="utf-8") as f:
            api_tpl_dict = json.loads(f.read())
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
            ]
        if target != "a":
            if not any([work_dir.joinpath(mod).is_dir() for mod in [
                "app/schemas",
                "app/models",
            ]]):  # is light
                target = "light"
                tpl_mods = [
                    "app/api",
                    "app/services",
                ]
        for mod in tpl_mods:
            if not work_dir.joinpath(mod).is_dir():
                sys.stderr.write(f"[error] not exists: {mod.replace('/', os.sep)}")
                sys.exit(1)
        for name in self.args.name.split(","):
            sys.stdout.write(f"Adding api:\n")
            flags = {
                # - 键：目标是否存在: 0-不存在，1-存在
                # - 值：创建是否关联: 0-不关联，1-关联
                #   - 创建a时，如果se存在为0，不存在为1
                #   - 创建se时，如果sc存在为0，不存在为1
                #   - 创建sc时，全为1
                #   - 创建m时，全为1
                #   - light:
                #       - 创建a时，如果se存在为0，不存在为1
                #       - 创建se时，如果a存在为0，不存在为1
                # a (a)
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
                # asm (a, se, sc, m)
                "0000": [1, 1, 1, 1],
                "0001": [1, 1, 1, 1],
                "0010": [1, 0, 1, 1],
                "0011": [1, 0, 1, 1],
                "0100": [0, 1, 1, 1],
                "0101": [0, 1, 1, 1],
                "0110": [0, 0, 1, 1],
                "0111": [0, 0, 1, 1],
                "1000": [1, 1, 1, 1],
                "1001": [1, 1, 1, 1],
                "1010": [1, 0, 1, 1],
                "1011": [1, 0, 1, 1],
                "1100": [0, 1, 1, 1],
                "1101": [0, 1, 1, 1],
                "1110": [0, 0, 1, 1],
                "1111": [0, 0, 1, 1],
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
                                with open(curr_mod_dir.joinpath("__init__.py"), "w+", encoding="utf-8") as f:
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
                    with open(curr_mod_dir.joinpath("__init__.py"), "w+", encoding="utf-8") as f:
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
                    with open(curr_mod_file, "w+", encoding="utf-8") as f:
                        sys.stdout.write(f"[{name}] Writing {curr_mod_file_rel}\n")
                        prefix = f"{target}_" if p_flag[i] else "only_"
                        k = prefix + mod.replace("/", "_") + ".py"
                        if subdir:
                            v = api_tpl_dict.get(k, "").replace(
                                "from app.schemas.tpl import (", f"from app.schemas.{subdir}.tpl import ("
                            ).replace(
                                "from app.services.tpl import (", f"from app.services.{subdir}.tpl import ("
                            ).replace(
                                "from app.models.tpl import (", f"from app.models.{subdir}.tpl import ("
                            ).replace(
                                "tpl", name).replace(
                                "Tpl", "".join([i[0].upper() + i[1:] if i else "_" for i in name.split("_")]))
                        else:
                            v = api_tpl_dict.get(k, "").replace(
                                "tpl", name).replace(
                                "Tpl", "".join([i[0].upper() + i[1:] if i else "_" for i in name.split("_")]))
                        f.write(v)


if __name__ == "__main__":
    main()
