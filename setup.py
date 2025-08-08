"""
@author axiner
@version v1.0.0
@created 2024/07/29 22:22
@abstract
@description
@history
"""
import os
import re
from pathlib import Path
from shutil import rmtree

from setuptools import setup, Command

here = Path(__file__).absolute().parent
pkg_name = "fastapi_scaff"


class BuildCommand(Command):
    description = "Build the package(.whl)"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self._clean_dist_dirs()
        self._update_version()
        os.system("python -m build --wheel --no-isolation")

    @staticmethod
    def _clean_dist_dirs():
        for path in ["dist", "build", f"{pkg_name}.egg-info"]:
            try:
                rmtree(here / path)
            except FileNotFoundError:
                pass

    @staticmethod
    def _update_version():
        with open(".history", "r", encoding="utf8") as f:
            __version__ = None
            for line in f:
                if line.startswith("## "):
                    __version__ = line.replace("## ", "").strip(" \nv")
                    break
            if not __version__:
                raise ValueError("Please set version")
        init_file = here.joinpath(f"{pkg_name}/__init__.py")
        with open(init_file, "r", encoding="utf8") as f:
            content = f.read()
        with open(init_file, "w", encoding="utf8", newline="\n") as f:
            content = re.sub(r'__version__ = "[\d.]+"', rf'__version__ = "{__version__}"', content)
            f.write(content)


class PublishCommand(Command):
    description = "Publish the package(.whl)"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system("python setup.py bld")
        os.system("python -m twine upload dist/*")


setup(
    cmdclass={
        "bld": BuildCommand,
        "pub": PublishCommand,
    },
    options={
        "bdist": {"plat_name": "any"},
    },
)
