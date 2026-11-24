"""路由自动注册测试：覆盖跳过、递归深度、导入失败与空路由边界。"""

import importlib
import sys
from types import ModuleType

import pytest
from fastapi import APIRouter, FastAPI

import app.api as api_module


def _module(name, **attrs):
    mod = ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


def _patch_import(monkeypatch, modules):
    original = importlib.import_module

    def fake_import(name):
        if name in modules:
            mod = modules[name]
            monkeypatch.setitem(sys.modules, name, mod)
            return mod
        return original(name)

    monkeypatch.setattr(api_module.importlib, "import_module", fake_import)


def test_register_routers_skips_inactive_module(monkeypatch, tmp_path):
    (tmp_path / "inactive.py").write_text("router = APIRouter()\n", encoding="utf-8")
    inactive = _module("fakeapi.inactive", router=APIRouter(), _active=False)
    _patch_import(monkeypatch, {"fakeapi.inactive": inactive})

    app = FastAPI()
    before = len(app.routes)
    api_module.register_routers(app, mod_dir=tmp_path, mod_base="fakeapi", min_depth=0, max_depth=2)

    assert len(app.routes) == before
    assert "fakeapi.inactive" not in sys.modules


def test_register_routers_respects_max_depth(monkeypatch, tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "router.py").write_text("router = APIRouter()\n", encoding="utf-8")
    modules = {
        "fakeapi.a": _module("fakeapi.a"),
        "fakeapi.a.b": _module("fakeapi.a.b"),
        "fakeapi.a.b.router": _module("fakeapi.a.b.router", router=APIRouter()),
    }
    _patch_import(monkeypatch, modules)

    app = FastAPI()
    before = len(app.routes)
    api_module.register_routers(app, mod_dir=tmp_path, mod_base="fakeapi", min_depth=1, max_depth=1)

    assert len(app.routes) == before
    assert "fakeapi.a.b.router" not in sys.modules


def test_register_routers_wraps_import_error(monkeypatch, tmp_path):
    (tmp_path / "broken.py").write_text("router = APIRouter()\n", encoding="utf-8")
    original = importlib.import_module

    def fake_import(name):
        if name == "fakeapi.broken":
            raise ImportError("missing dependency")
        return original(name)

    monkeypatch.setattr(api_module.importlib, "import_module", fake_import)

    with pytest.raises(RuntimeError, match=r"fakeapi\.broken"):
        api_module.register_routers(FastAPI(), mod_dir=tmp_path, mod_base="fakeapi", min_depth=0, max_depth=2)


def test_register_routers_allows_router_without_routes(monkeypatch, tmp_path):
    (tmp_path / "empty.py").write_text("router = APIRouter()\n", encoding="utf-8")
    empty = _module("fakeapi.empty", router=APIRouter())
    _patch_import(monkeypatch, {"fakeapi.empty": empty})

    app = FastAPI()
    before = len(app.routes)
    api_module.register_routers(app, mod_dir=tmp_path, mod_base="fakeapi", min_depth=0, max_depth=2)

    assert len(app.routes) >= before
