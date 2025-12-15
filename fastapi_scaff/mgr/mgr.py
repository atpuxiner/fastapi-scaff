import base64
import json
import re
from pathlib import Path

from toollib.utils import listfile

project_dir = Path(__file__).absolute().parent.parent.parent
pkg_mod_name = "fastapi_scaff"


def gen_project_json():
    exclude_pat = re.compile('|'.join([
        "^.git(/.*)?$",
        "^.idea(/.*)?$",
        "^.vscode(/.*)?$",
        "^build(/.*)?$",
        "^dist(/.*)?$",
        "^fastapi_scaff(/.*)?$",
        "^fastapi_scaff.egg-info(/.*)?$",
        "^.history$",
        "^pyproject.toml$",
        "^setup.py$",
        # #
        ".pyc$",
        ".log$",
        ".sqlite3?$",
    ]))
    data = {}
    for file in listfile(project_dir, is_r=True):
        file_str = file.as_posix().replace(project_dir.as_posix(), "").lstrip("/")
        if not exclude_pat.search(file_str):
            if file.suffix == ".jpg":
                with open(file, "rb") as f:
                    data[file_str] = base64.b64encode(f.read()).decode('utf-8')
            else:
                with open(file, "r", encoding="utf-8") as f:
                    data[file_str] = f.read()
    for m in [
        "_tiny",
        "_single"
    ]:
        for file in listfile(m):
            with open(file, "r", encoding="utf-8") as f:
                data[f"app/{m[1:]}_{file.name}"] = f.read()
    with open(project_dir.joinpath(f"{pkg_mod_name}/_project_tpl.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def gen_api_json():
    data = {}
    _api_tpl = project_dir.joinpath(f"{pkg_mod_name}/mgr/_api_tpl")
    for file in listfile(_api_tpl):
        with open(file, "r", encoding="utf-8") as f:
            data[file.name] = f.read()
    with open(project_dir.joinpath(f"{pkg_mod_name}/_api_tpl.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def run():
    gen_project_json()
    gen_api_json()


if __name__ == '__main__':
    run()
