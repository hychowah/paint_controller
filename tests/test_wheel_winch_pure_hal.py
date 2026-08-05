"""Level C P3: pure wheel/winch HAL + shell contracts."""

from __future__ import annotations

import threading

from paint_controller.controllers.wheel import WheelHal, WheelStatusSnapshot
from paint_controller.controllers.winch import WinchHal
from paint_controller.ports.notifier import RecordingDeviceNotifier


def test_wheel_hal_notifies_without_pyside(fake_node) -> None:
    rec = RecordingDeviceNotifier()
    hal = WheelHal(fake_node, notifier=rec)
    hal.set_left_wheel_speed(1.0)
    assert rec.names == ["left_wheel_speed_changed"]
    # Continuous-zero e-stop (product traffic kind).
    assert hal.emergency_stop() is None
    assert hal._last_left_rpm == 0 and hal._last_right_rpm == 0


def test_wheel_shell_error_signal_and_bridge_parent(qt_app, fake_node) -> None:
    from paint_controller.controllers.wheel_shell import WheelController

    wheel = WheelController(fake_node)
    assert wheel._telemetry.parent() is wheel
    errors: list[tuple[bool, str]] = []
    wheel.error_state_changed.connect(lambda e, m: errors.append((e, m)))

    snap = WheelStatusSnapshot(
        recv_mono=0.0,
        left_available=True,
        right_available=True,
        left_error=True,
        right_error=False,
        left_speed=0.0,
        right_speed=0.0,
        left_current=0.0,
        right_current=0.0,
        left_travel_mm=0.0,
        right_travel_mm=0.0,
    )
    wheel._apply_status_snapshot(snap)
    assert errors == [(True, "Left track motor error")]
    wheel.cleanup()


def test_wheel_shell_status_bridge_applies_on_main(qt_app, fake_node) -> None:
    from paint_controller.controllers.wheel_shell import WheelController

    main_tid = threading.get_ident()
    wheel = WheelController(fake_node)
    tids: list[int] = []
    wheel.left_wheel_speed_changed.connect(lambda: tids.append(threading.get_ident()))

    def worker() -> None:
        wheel._telemetry.post(
            WheelStatusSnapshot(
                recv_mono=1.0,
                left_available=True,
                right_available=True,
                left_error=False,
                right_error=False,
                left_speed=9.0,
                right_speed=0.0,
                left_current=0.0,
                right_current=0.0,
                left_travel_mm=0.0,
                right_travel_mm=0.0,
            )
        )

    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=5)
    assert wheel.left_wheel_speed == 0.0
    qt_app.processEvents()
    assert wheel.left_wheel_speed == 9.0
    assert tids == [main_tid]
    wheel.cleanup()


def test_winch_shell_settings_inject_without_hal_connect(qt_app, fake_node) -> None:
    from PySide6.QtCore import QObject, Signal

    from paint_controller.controllers.winch_shell import WinchController

    class FakeSettings(QObject):
        winch_max_speed_mmps_changed = Signal(float)

        def get(self, key, default=None):
            if key == "winch_max_speed_mmps":
                return 250.0
            return default

    settings = FakeSettings()
    winch = WinchController(fake_node, settings_manager=settings)
    assert winch._max_speed == 250.0
    settings.winch_max_speed_mmps_changed.emit(300.0)
    assert winch._max_speed == 300.0
    # Pure HAL has no SettingsManager attribute
    assert not hasattr(winch.hal, "_settings_manager")
    winch.cleanup()


def test_winch_hal_notifies(fake_node) -> None:
    rec = RecordingDeviceNotifier()
    # pure path without bridge
    hal = WinchHal(fake_node, notifier=rec)
    hal.set_available(True)
    rec.names.clear()
    hal.set_cable_length(12.5)
    assert rec.names == ["cable_length_changed"]
    assert hal.cable_length == 12.5
