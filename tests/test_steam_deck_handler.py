"""Regression tests for SteamDeckHandler shutdown cleanup."""

from __future__ import annotations

import importlib
import sys
import types


def _install_hid_stub() -> None:
    if "hid" in sys.modules:
        return

    hid_mod = types.ModuleType("hid")

    class _FakeDevice:
        def open_path(self, _path):
            pass

        def set_nonblocking(self, _value):
            pass

        def read(self, _size):
            return []

        def close(self):
            pass

    hid_mod.device = _FakeDevice
    hid_mod.enumerate = lambda *_args, **_kwargs: []
    sys.modules["hid"] = hid_mod


class _FakeTimer:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True

    def deleteLater(self) -> None:
        pass


class _FakeReaderThread:
    def __init__(self) -> None:
        self.cleanup_calls = 0

    def isRunning(self) -> bool:
        return True

    def cleanup(self) -> None:
        self.cleanup_calls += 1


def test_cleanup_uses_full_reader_thread_cleanup(monkeypatch):
    _install_hid_stub()
    module = importlib.import_module("paint_controller.handlers.steam_deck")
    handler = module.SteamDeckHandler()

    fake_timer = _FakeTimer()
    fake_reader_thread = _FakeReaderThread()
    stop_calls = []

    monkeypatch.setattr(handler, "_availability_timer", fake_timer)
    monkeypatch.setattr(handler, "_reader_thread", fake_reader_thread)
    monkeypatch.setattr(handler, "stop", lambda: stop_calls.append(True))

    handler.cleanup()

    assert stop_calls == [True]
    assert fake_timer.stopped is True
    assert handler._availability_timer is None
    assert fake_reader_thread.cleanup_calls == 1