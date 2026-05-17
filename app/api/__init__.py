"""
接口
"""

import importlib
import logging
import re
import sys
from pathlib import Path

from fastapi import APIRouter, FastAPI

from app import APP_DIR

_API_MOD_DIR = APP_DIR.joinpath("api")
_API_MOD_BASE = "app.api"

logger = logging.getLogger(__name__)


def register_routers(
    app: FastAPI,
    mod_dir: Path = _API_MOD_DIR,
    mod_base: str = _API_MOD_BASE,
    router_reg: str = r"^\s*((?:[a-zA-Z_]\w*)?_router|router)\s*=\s*APIRouter\s*\(",
    prefix: str = "",
    depth: int = 0,
    min_depth: int = 1,
    max_depth: int = 2,
):
    """
    注册路由
    要求：
        路由模块：非'__'开头
        路由名称：{router|xxx_router}
    :param app: FastAPI应用
    :param mod_dir: api模块目录
    :param mod_base: api模块基础
    :param router_reg: 路由对象正则
    :param prefix: url前缀
    :param depth: 当前递归深度
    :param min_depth: 最小递归深度
    :param max_depth: 最大递归深度
    """
    if depth > max_depth:
        return

    router_pat = re.compile(router_reg, re.MULTILINE)
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
            except ImportError as e:
                raise RuntimeError(f"Register router failed to import module: {new_mod_base} ({e})") from e
            register_routers(
                app=app,
                mod_dir=new_mod_dir,
                mod_base=new_mod_base,
                prefix=new_prefix,
                router_reg=router_reg,
                depth=depth + 1,
                max_depth=max_depth,
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
                prefix_str = prefix.replace("//", "/").rstrip("/")
                for match in router_pat.finditer(item.read_text(encoding="utf-8")):
                    router = getattr(mod, match.group(1), None)
                    if not isinstance(router, APIRouter):
                        continue
                    if router.tags or getattr(router.routes[0], "tags", None):
                        tags = None
                    else:
                        tags = [getattr(mod, "_tag", None) or (item.parent.stem if depth > 1 else mod_name)]
                    app.include_router(router=router, prefix=prefix_str, tags=tags)
            except ImportError as e:
                raise RuntimeError(f"Register router failed to import module: {final_mod} ({e})") from e
