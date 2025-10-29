import json
import re
from pathlib import Path

from toollib.utils import listfile

project_dir = Path(__file__).absolute().parent.parent.parent
pkg_mod_name = "fastapi_scaff"


def gen_project_json():
    include_mods_comp = re.compile('|'.join([
        "app",
        "app_celery",
        "config",
        "deploy",
        "docs",
        "logs",
        "tests",
        ".gitignore",
        ".python-version",
        "LICENSE",
        "README.md",
        "requirements.txt",
        "runcbeat.py",
        "runcworker.py",
        "runserver.py",
    ]))
    exclude_exts_comp = re.compile('|'.join([
        ".pyc$",
        ".log$",
        ".sqlite3?$",
    ]))
    data = {}
    for file in listfile(project_dir, is_r=True):
        file_str = file.as_posix().replace(project_dir.as_posix(), "").lstrip("/")
        if include_mods_comp.search(file_str.split("/")[0]) and not exclude_exts_comp.search(file_str):
            with open(file, "r", encoding="utf-8") as f:
                data[file_str] = f.read()
    with open("_micro_sp/initializer.py", "r", encoding="utf-8") as f:
        data["app/initializer.py"] = f.read()
    with open("_micro_sp/middleware.py", "r", encoding="utf-8") as f:
        data["app/middleware.py"] = f.read()
    with open(project_dir.joinpath(f"{pkg_mod_name}/_project_tpl.json"), "w+", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def gen_api_json():
    data = {}
    _api_tpl = project_dir.joinpath(f"{pkg_mod_name}/mgr/_api_tpl")
    for file in listfile(_api_tpl):
        with open(file, "r", encoding="utf-8") as f:
            data[file.name] = f.read()
    with open(project_dir.joinpath(f"{pkg_mod_name}/_api_tpl.json"), "w+", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def run():
    gen_project_json()
    gen_api_json()


if __name__ == '__main__':
    run()
