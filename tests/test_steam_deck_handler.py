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


def test_button_held_emits_after_hold_threshold(monkeypatch, qt_app):
    """TD-039: button_held must still fire (now collected under lock, emitted after unlock)."""
    _install_hid_stub()
    module = importlib.import_module("paint_controller.handlers.steam_deck")
    handler = module.SteamDeckHandler()

    held: list[tuple[str, float]] = []
    handler.button_held.connect(lambda button, duration: held.append((button, duration)))
    handler.register_button_hold_callback("a", 0.05, lambda _duration: None)

    t0 = 1000.0
    times = iter([t0, t0 + 0.01, t0 + 0.1, t0 + 0.11])
    monkeypatch.setattr(module.time, "time", lambda: next(times, t0 + 1.0))

    def _frame(a_pressed: bool) -> dict:
        return {
            "buttons": {
                "up": False,
                "down": False,
                "left": False,
                "right": False,
                "a": a_pressed,
                "b": False,
                "x": False,
                "y": False,
                "l1": False,
                "r1": False,
                "l4": False,
                "r4": False,
                "l5": False,
                "r5": False,
                "l3": False,
                "menu": False,
                "switch": False,
                "steam": False,
                "dot": False,
            },
            "imu": {"pitch": 0.0, "roll": 0.0, "yaw": 0.0},
            "triggers": {"left": 0.0, "right": 0.0},
            "sticks": {
                "left": {"x": 0.0, "y": 0.0},
                "right": {"x": 0.0, "y": 0.0},
            },
        }

    frames = iter([_frame(True), _frame(True)])
    monkeypatch.setattr(module, "parse_hid_frame", lambda _data: next(frames))

    handler._process_input(b"\x00")
    handler._process_input(b"\x00")

    assert len(held) == 1
    assert held[0][0] == "a"
    assert held[0][1] >= 0.05
    handler.cleanup()
