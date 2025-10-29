"""
api
"""
import importlib
import sys
from pathlib import Path

from fastapi import FastAPI, APIRouter
from loguru import logger

from app import APP_DIR

_API_MOD_DIR = APP_DIR.joinpath("api")
_API_MOD_BASE = "app.api"


def register_routers(
        app: FastAPI,
        mod_dir: Path = _API_MOD_DIR,
        mod_base: str = _API_MOD_BASE,
        name: str = "router",
        prefix: str = "",
        depth: int = 0,
        min_depth: int = 1,
        max_depth: int = 2,
):
    """
    注册路由
    要求：
        路由模块：非'__'开头的模块
        路由名称：{name}
    :param app: FastAPI应用
    :param mod_dir: api模块目录
    :param mod_base: api模块基础
    :param name: 路由名称
    :param prefix: url前缀
    :param depth: 当前递归深度
    :param min_depth: 最小递归深度
    :param max_depth: 最大递归深度
    """
    if depth > max_depth:
        return
    for item in mod_dir.iterdir():
        if item.name.startswith("__"):
            continue
        if item.is_dir():
            new_mod_dir = item
            new_mod_base = f"{mod_base}.{item.name}"
            new_prefix = prefix
            try:
                mod = importlib.import_module(new_mod_base)
                _prefix = getattr(mod, "_prefix", None)
                if _prefix:
                    new_prefix = f"{new_prefix}/{_prefix}"
            except ImportError:
                logger.error(f"Register router failed to import module: {new_mod_base}")
                continue
            register_routers(
                app=app,
                mod_dir=new_mod_dir,
                mod_base=new_mod_base,
                prefix=new_prefix,
                name=name,
                depth=depth + 1,
                max_depth=max_depth
            )
        elif item.is_file() and item.suffix == ".py" and depth >= min_depth:
            mod_name = item.stem
            final_mod = f"{mod_base}.{mod_name}"
            try:
                mod = importlib.import_module(final_mod)
                if not getattr(mod, "_active", True):
                    logger.info(f"Register router skipping inactive module: {final_mod}")
                    sys.modules.pop(final_mod)
                    continue
                if router := getattr(mod, name, None):
                    if isinstance(router, APIRouter):
                        tag = getattr(mod, "_tag", None)
                        if not tag:
                            tag = item.parent.stem if depth > 1 else mod_name
                        app.include_router(
                            router=router,
                            prefix=prefix.replace("//", "/").rstrip("/"),
                            tags=[tag]
                        )
            except ImportError as e:
                logger.error(f"Register router failed to import module: {final_mod} ({e})")
                continue
