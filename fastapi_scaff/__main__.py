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
               "  `new`: %(prog)s new myproj -d postgresql\n"
               "  `add`: %(prog)s add myapi",
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
        default="abd",
        choices=["a", "ab", "abd"],
        metavar="",
        help="`add`时可指定目标(默认abd, a:api,b:business,d:datatype)")
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
                         f"> ----- more see README.md -----\n")

    @staticmethod
    def _db_requirements_map(name: str):
        return {
            "default": "aiosqlite==0.21.0",
            "sqlite": [
                "aiosqlite==0.21.0",
            ],
            "mysql": [
                "PyMySQL==1.1.1",
                "aiomysql==0.2.0",
            ],
            "postgresql": [
                "psycopg2-binary==2.9.10",
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
                "db_url": "db_url: mysql+pymysql://<username>:<password>@<host>:<port>/app_dev?charset=utf8mb4",
                "db_async_url": "db_async_url: mysql+aiomysql://<username>:<password>@<host>:<port>/app_dev?charset=utf8mb4",
            },
            "postgresql": {
                "db_url": "db_url: postgresql://<username>:<password>@<host>:<port>/app_dev",
                "db_async_url": "db_async_url: postgresql+asyncpg://<username>:<password>@<host>:<port>/app_dev",
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
        elif target == "ab":
            tpl_mods = [
                "app/api",
                "app/business",
            ]
        else:
            tpl_mods = [
                "app/api",
                "app/business",
                "app/datatype",
            ]
        for mod in tpl_mods:
            if not work_dir.joinpath(mod).is_dir():
                sys.stderr.write(f"[error] not exists: {mod.replace('/', os.sep)}")
                sys.exit(1)
        for name in self.args.name.split(","):
            sys.stdout.write(f"Adding api:\n")
            flags = {
                # a
                "0": [0],
                "1": [0],
                # ab
                "00": [0, 0],
                "10": [0, 1],
                "01": [1, 0],
                "11": [0, 0],
                # abd
                "000": [0, 0, 0],
                "100": [0, 0, 0],
                "010": [1, 0, 0],
                "001": [0, 1, 0],
                "110": [0, 0, 0],
                "101": [0, 1, 0],
                "011": [1, 0, 0],
                "111": [0, 0, 0],
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
                        prefix = "only_" if p_flag[i] else f"{target}_"
                        k = prefix + mod.replace("/", "_") + ".py"
                        if subdir:
                            v = api_tpl_dict.get(k, "").replace(
                                "from app.business.tpl import (", f"from app.business.{subdir}.tpl import ("
                            ).replace(
                                "from app.datatype.tpl import (", f"from app.datatype.{subdir}.tpl import ("
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
