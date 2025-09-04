"""
api
"""
import importlib
import sys
from pathlib import Path

from fastapi import FastAPI
from loguru import logger

from app import APP_DIR

_API_MOD_DIR = APP_DIR.joinpath("api")
_API_MOD_BASE = "app.api"


def register_routers(
        app: FastAPI,
        mod_dir: Path = _API_MOD_DIR,
        mod_base: str = _API_MOD_BASE,
        prefix: str = "",
        obj_suffix: str = "_router",
        depth: int = 0,
        max_depth: int = 2
):
    """
    注册路由
    要求：
        路由模块：非'__'开头的模块
        路由对象：{模块名称}{路由对象后缀}
    :param app: FastAPI应用
    :param mod_dir: api模块目录
    :param mod_base: api模块基础
    :param prefix: url前缀
    :param obj_suffix: 路由对象后缀
    :param depth: 当前递归深度
    :param max_depth: 最大递归深度
    """
    if depth > max_depth:
        return
    for item in mod_dir.iterdir():
        if item.name.startswith("__") or item.name == "__pycache__":
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
                obj_suffix=obj_suffix,
                depth=depth + 1,
                max_depth=max_depth
            )
        elif item.is_file() and item.suffix == ".py" and depth > 0:
            mod_name = item.stem
            final_mod = f"{mod_base}.{mod_name}"
            try:
                mod = importlib.import_module(final_mod)
                if not getattr(mod, "_active", True):
                    logger.info(f"Register router skipping inactive module: {final_mod}")
                    sys.modules.pop(final_mod)
                    continue
                router_name = f"{mod_name}{obj_suffix}"
                if router := getattr(mod, router_name, None):
                    tag = getattr(mod, "_tag", None)
                    if not tag:
                        tag = item.parent.stem if depth > 1 else mod_name
                    app.include_router(
                        router=router,
                        prefix=prefix.replace("//", "/").rstrip("/"),
                        tags=[tag]
                    )
            except ImportError:
                logger.error(f"Register router failed to import module: {final_mod}")
                continue
