"""Celery 生产/消费测试：不依赖真实 broker，覆盖注册表、选项合并与任务执行。"""

from types import SimpleNamespace

import pytest

import celery_app.consumer as consumer
from celery_app.consumer.tasks import health as health_module
from celery_app.producer import publisher


def test_publish_uses_registry_and_merges_options(monkeypatch):
    captured = {}

    def fake_send_task(name, **kwargs):
        captured.update(kwargs)
        captured["name"] = name
        return SimpleNamespace(id="task-123")

    monkeypatch.setattr(publisher.celery_app, "send_task", fake_send_task)

    result = publisher.publish(
        "health",
        task_args=("ping",),
        task_kwargs={"count": 1},
        task_id="custom-id",
        expires=60,
    )

    assert result == "task-123"
    assert captured["name"] == "celery_app.consumer.tasks.health.health"
    assert captured["queue"] == "health"
    assert captured["args"] == ("ping",)
    assert captured["kwargs"] == {"count": 1}
    assert captured["task_id"] == "custom-id"
    assert captured["expires"] == 60


def test_publish_does_not_leak_options_between_calls(monkeypatch):
    seen = []

    def fake_send_task(name, **kwargs):
        seen.append(kwargs)
        return SimpleNamespace(id="task")

    monkeypatch.setattr(publisher.celery_app, "send_task", fake_send_task)
    publisher.publish("health", expires=10)
    publisher.publish("health")

    assert seen[0]["expires"] == 10
    assert "expires" not in seen[1]


def test_publish_rejects_unknown_task():
    with pytest.raises(ValueError, match="UNKNOWN TASK"):
        publisher.publish("not-registered")


def test_health_task_logs_message(monkeypatch):
    messages = []
    monkeypatch.setattr(health_module.logger, "info", lambda msg: messages.append(msg))

    health_module.health.run("ping")

    assert messages == ["OK: ping"]


def test_autodiscover_task_modules_skips_inactive(monkeypatch, tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "active.py").write_text("", encoding="utf-8")
    (tasks_dir / "inactive.py").write_text("_active = False\n", encoding="utf-8")
    (tasks_dir / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(consumer, "__file__", str(tmp_path / "__init__.py"))

    assert consumer.autodiscover_task_modules() == ["celery_app.consumer.tasks.active"]
