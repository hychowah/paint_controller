"""Tests for paint_controller.controllers.ssh."""

from __future__ import annotations

import importlib
import json
import sys
import types


def _install_paramiko_stub(monkeypatch):
    state = {
        "connect_calls": [],
        "policy": None,
        "command": None,
        "closed": False,
    }

    class FakeStream:
        def __init__(self, data: str) -> None:
            self._data = data

        def read(self) -> bytes:
            return self._data.encode()

    class FakeSSHClient:
        def set_missing_host_key_policy(self, policy) -> None:
            state["policy"] = policy

        def connect(self, hostname, **kwargs) -> None:
            state["connect_calls"].append((hostname, kwargs))

        def exec_command(self, command):
            state["command"] = command
            return None, FakeStream("ok"), FakeStream("")

        def close(self) -> None:
            state["closed"] = True

    fake_paramiko = types.SimpleNamespace(
        SSHClient=FakeSSHClient,
        AutoAddPolicy=lambda: "auto-policy",
        RSAKey=types.SimpleNamespace(from_private_key_file=lambda path: f"key:{path}"),
    )
    monkeypatch.setitem(sys.modules, "paramiko", fake_paramiko)
    sys.modules.pop("paint_controller.controllers.ssh", None)
    return state


def test_ssh_launcher_uses_timeouts_and_daemon_thread(monkeypatch):
    state = _install_paramiko_stub(monkeypatch)
    ssh_module = importlib.import_module("paint_controller.controllers.ssh")

    class ImmediateThread:
        def __init__(self, *, target, daemon):
            self._target = target
            self.daemon = daemon
            self.started = False

        def start(self):
            self.started = True
            self._target()

        def is_alive(self):
            return False

        def join(self, timeout=None):
            return None

    monkeypatch.setattr(ssh_module.threading, "Thread", ImmediateThread)

    launcher = ssh_module.SSHLauncher("10.0.0.2", "deck", password="secret", port=2200)
    thread = launcher.run_script("echo ok")

    assert thread.daemon is True
    assert thread.started is True
    assert state["connect_calls"] == [
        (
            "10.0.0.2",
            {
                "port": 2200,
                "username": "deck",
                "password": "secret",
                "timeout": 5,
                "banner_timeout": 5,
                "auth_timeout": 5,
            },
        )
    ]
    assert state["command"] == "echo ok"
    assert state["closed"] is True


def test_save_json_file_keeps_last_good_file_when_dump_fails(monkeypatch, tmp_path, qt_app):
    _install_paramiko_stub(monkeypatch)
    ssh_module = importlib.import_module("paint_controller.controllers.ssh")
    controller = ssh_module.UISSHController()
    try:
        config_path = tmp_path / "ssh_config.json"
        config_path.write_text(json.dumps({"device": {"hostname": "1.2.3.4"}}))

        def faulty_dump(payload, handle, indent=4):
            handle.write('{"broken": ')
            raise RuntimeError("simulated write failure")

        monkeypatch.setattr(ssh_module.json, "dump", faulty_dump)

        assert controller._save_json_file(str(config_path), {"device": {"hostname": "5.6.7.8"}}) is False
        assert json.loads(config_path.read_text()) == {"device": {"hostname": "1.2.3.4"}}
        assert list(config_path.parent.glob("*.tmp")) == []
    finally:
        controller.cleanup()


def test_availability_callback_ignores_runtime_error_during_teardown(monkeypatch, qt_app):
    _install_paramiko_stub(monkeypatch)
    ssh_module = importlib.import_module("paint_controller.controllers.ssh")
    controller = ssh_module.UISSHController()
    try:

        class BrokenSignal:
            def emit(self, *args, **kwargs) -> None:
                raise RuntimeError("Signal source has been deleted")

        monkeypatch.setattr(controller, "availabilityResultReady", BrokenSignal(), raising=False)
        monkeypatch.setattr(
            controller.thread_pool,
            "start",
            lambda runnable: runnable.callback("device", False, "late result", 0.0),
        )

        controller._check_device_availability("device", "10.0.0.2")
    finally:
        controller.cleanup()


def test_cleanup_stops_timers_and_waits_for_workers(monkeypatch, qt_app):
    _install_paramiko_stub(monkeypatch)
    ssh_module = importlib.import_module("paint_controller.controllers.ssh")
    controller = ssh_module.UISSHController()
    events = []

    class FakePool:
        def clear(self):
            events.append("clear")

        def waitForDone(self, timeout):
            events.append(("wait", timeout))
            return True

    class FakeThread:
        def join(self, timeout=None):
            events.append(("join", timeout))

        def is_alive(self):
            return True

    monkeypatch.setattr(controller, "_stop_all_availability_checks", lambda: events.append("stop"))
    monkeypatch.setattr(controller, "thread_pool", FakePool(), raising=False)
    monkeypatch.setattr(controller, "_prune_command_threads", lambda: None)
    controller._command_threads = [FakeThread(), FakeThread()]

    controller.cleanup()

    assert controller._is_cleaning_up is True
    assert events == ["stop", "clear", ("wait", 3000), ("join", 2), ("join", 2)]
