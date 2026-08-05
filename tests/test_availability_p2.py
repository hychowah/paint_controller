"""Level C P2: pure AvailabilityState + watchdog + bridge shell parenting."""

from __future__ import annotations

import time

from paint_controller.core.availability import AvailabilityState


def test_availability_state_set_and_freshness() -> None:
    state = AvailabilityState(connection_timeout=1.0)
    assert state.available is False
    assert state.set_available(True) is True
    assert state.set_available(True) is False
    assert state.available is True

    now = time.time()
    state.record_status_update(now)
    assert state.status_is_recent(now + 0.5) is True
    assert state.status_is_recent(now + 1.5) is False
    assert state.time_since_last_status(now + 2.0) == 2.0


def test_availability_watchdog_ticks(qt_core_app) -> None:
    from paint_controller.core.availability_watchdog import AvailabilityWatchdog

    hits: list[int] = []
    dog = AvailabilityWatchdog(lambda: hits.append(1), interval_ms=1)
    assert dog.is_active is True
    # Drive timer via processEvents + small sleeps
    deadline = time.time() + 1.0
    while time.time() < deadline and len(hits) < 2:
        qt_core_app.processEvents()
        time.sleep(0.01)
    dog.stop()
    assert len(hits) >= 1
    assert dog.is_active is False


def test_wheel_bridge_and_watchdog_parented_to_io_shell(qt_app, fake_node) -> None:
    from paint_controller.controllers.wheel_shell import WheelController
    from paint_controller.core.device_io_shell import DeviceIoShell

    shell = DeviceIoShell("wheel-test")
    wheel = WheelController(fake_node, io_shell=shell)
    assert wheel.io_shell is shell
    assert wheel._telemetry.parent() is shell
    assert wheel._watchdog is not None
    assert wheel._watchdog.parent() is shell
    assert wheel._telemetry.parent() is not wheel
    wheel.cleanup()


def test_winch_and_teensy_bridge_parent_is_shell(qt_app, fake_node) -> None:
    from paint_controller.controllers.teensy import TeensyController
    from paint_controller.controllers.winch_shell import WinchController

    winch = WinchController(fake_node)
    teensy = TeensyController(fake_node)
    # P3 winch shell is its own lifetime parent; teensy still uses DeviceIoShell.
    assert winch._telemetry.parent() is winch.io_shell
    assert teensy._telemetry.parent() is teensy.io_shell
    assert teensy._telemetry.parent() is not teensy
    winch.cleanup()
    teensy.cleanup()


def test_wheel_availability_timeout_still_works(qt_app, fake_node) -> None:
    from paint_controller.controllers.wheel_shell import WheelController

    controller = WheelController(fake_node)
    controller._left_motor_available = True
    controller._right_motor_available = True
    controller.set_available(True)
    controller._last_status_update_time = time.time() - 2.0
    controller._check_availability()
    assert controller.available is False
    controller.cleanup()
