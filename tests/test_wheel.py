"""Tests for paint_controller.controllers.wheel.WheelController."""

from __future__ import annotations

import importlib
import time

from paint_controller.controllers.wheel import WheelStatusSnapshot


def _wheel_controller_class():
    return importlib.import_module("paint_controller.controllers.wheel_shell").WheelController


def _vehicle_status_class():
    return importlib.import_module("paint_interfaces.msg").VehicleStatus


def test_command_speed_publishes_unified_message(qt_app, fake_node):
    controller = _wheel_controller_class()(fake_node)

    assert controller.command_speed(120, -80) is True

    speed_msg = fake_node.publishers[0].published_messages[-1]
    assert speed_msg.left_rpm == 120
    assert speed_msg.right_rpm == -80


def test_command_bus_defers_raw_publish_until_pump(qt_app, fake_node):
    """TD-054: bound controller must not raw-publish until RosCommandBus.pump()."""
    from paint_controller.core.ros_io import RosCommandBus

    bus = RosCommandBus()
    controller = _wheel_controller_class()(fake_node, command_bus=bus)
    speed_pub = fake_node.publishers[0]

    assert controller.command_speed(120, -80) is True
    assert speed_pub.published_messages == []
    assert bus.pending_counts() == (0, 1)

    assert bus.pump() == 1
    assert len(speed_pub.published_messages) == 1
    assert speed_pub.published_messages[-1].left_rpm == 120
    assert speed_pub.published_messages[-1].right_rpm == -80

    # Continuous last-wins through bound handle.
    assert controller.command_speed(1, 2) is True
    assert controller.command_speed(3, 4) is True
    assert speed_pub.published_messages[-1].left_rpm == 120  # not pumped yet
    assert bus.pump() == 1
    assert speed_pub.published_messages[-1].left_rpm == 3
    assert speed_pub.published_messages[-1].right_rpm == 4


def test_left_and_right_speed_commands_reuse_last_partner_value(qt_app, fake_node):
    controller = _wheel_controller_class()(fake_node)

    assert controller.command_left_wheel_speed(90) is True
    first_msg = fake_node.publishers[0].published_messages[-1]
    assert first_msg.left_rpm == 90
    assert first_msg.right_rpm == 0

    assert controller.command_right_wheel_speed(-45) is True
    second_msg = fake_node.publishers[0].published_messages[-1]
    assert second_msg.left_rpm == 90
    assert second_msg.right_rpm == -45


def test_apply_status_snapshot_updates_properties(qt_app, fake_node):
    """Main-thread apply owns QObject fields (TD-056)."""
    controller = _wheel_controller_class()(fake_node)
    snap = WheelStatusSnapshot(
        recv_mono=time.time(),
        left_available=True,
        right_available=True,
        left_error=False,
        right_error=False,
        left_speed=11.5,
        right_speed=-9.0,
        left_current=4.2,
        right_current=4.4,
        left_travel_mm=150.0,
        right_travel_mm=175.0,
    )
    controller._apply_status_snapshot(snap)

    assert controller.available is True
    assert controller.left_motor_available is True
    assert controller.right_motor_available is True
    assert controller.left_wheel_speed == 11.5
    assert controller.right_wheel_speed == -9.0
    assert controller.left_wheel_current == 4.2
    assert controller.right_wheel_current == 4.4
    assert controller.left_wheel_position == 150.0
    assert controller.right_wheel_position == 175.0


def test_status_callback_does_not_mutate_fields_until_events(qt_app, fake_node):
    """Affinity: ROS callback only posts; apply runs after processEvents."""
    controller = _wheel_controller_class()(fake_node)
    status = _vehicle_status_class()(
        left_available=True,
        right_available=True,
        left_speed=11.5,
        right_speed=-9.0,
        left_current=4.2,
        right_current=4.4,
        left_travel_mm=150.0,
        right_travel_mm=175.0,
    )

    controller._status_callback(status)
    assert controller.available is False
    assert controller.left_motor_available is False
    assert controller.left_wheel_speed == 0.0

    qt_app.processEvents()

    assert controller.available is True
    assert controller.left_motor_available is True
    assert controller.left_wheel_speed == 11.5


def test_status_callback_from_worker_thread_defers_apply(qt_app, fake_node):
    """Real worker thread may call ROS callback; QObject fields apply only after main processEvents."""
    import threading

    controller = _wheel_controller_class()(fake_node)
    status = _vehicle_status_class()(
        left_available=True,
        right_available=True,
        left_speed=22.0,
        right_speed=-11.0,
        left_current=1.0,
        right_current=2.0,
        left_travel_mm=10.0,
        right_travel_mm=20.0,
    )
    errors: list[BaseException] = []
    main_tid = threading.get_ident()
    apply_tids: list[int] = []
    # Bridge captures apply_fn at construct time — wrap the bridge's target.
    orig_apply = controller._telemetry._apply_fn

    def tracking_apply(snap):
        apply_tids.append(threading.get_ident())
        return orig_apply(snap)

    controller._telemetry._apply_fn = tracking_apply

    def worker() -> None:
        try:
            controller._status_callback(status)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=worker, name="wheel-status-worker")
    thread.start()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert errors == []

    # Still default until main-thread apply.
    assert controller.available is False
    assert controller.left_motor_available is False
    assert controller.left_wheel_speed == 0.0
    assert apply_tids == []

    qt_app.processEvents()

    assert controller.available is True
    assert controller.left_motor_available is True
    assert controller.left_wheel_speed == 22.0
    assert controller.right_wheel_speed == -11.0
    assert apply_tids == [main_tid], f"apply must run on main thread, got {apply_tids}"


def test_error_signal_emits_on_main_after_worker_status_callback(qt_app, fake_node):
    """Worker posts status; error_state_changed must fire only after main processEvents."""
    import threading

    from PySide6.QtTest import QSignalSpy

    controller = _wheel_controller_class()(fake_node)
    spy = QSignalSpy(controller.error_state_changed)
    status = _vehicle_status_class()(
        left_available=True,
        right_available=True,
        left_error=True,
        right_error=False,
    )
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            controller._status_callback(status)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=worker, name="wheel-error-signal-worker")
    thread.start()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert errors == []

    # No signal until main apply.
    assert spy.count() == 0
    assert controller.left_error is False

    qt_app.processEvents()

    assert spy.count() == 1
    assert spy.at(0) == [True, "Left track motor error"]
    assert controller.left_error is True


def test_set_enabled_records_intent_and_publishes_inverted(qt_app, fake_node):
    controller = _wheel_controller_class()(fake_node)

    assert controller.enabled is False

    controller.setEnabled(True)
    assert controller.enabled is True
    disable_msg = fake_node.publishers[2].published_messages[-1]
    assert disable_msg.data is False

    controller.setEnabled(False)
    assert controller.enabled is False
    disable_msg = fake_node.publishers[2].published_messages[-1]
    assert disable_msg.data is True


def test_error_signal_emits_once_per_transition(qt_app, fake_node):
    controller = _wheel_controller_class()(fake_node)
    received = []
    controller.error_state_changed.connect(lambda has_error, message: received.append((has_error, message)))

    status = _vehicle_status_class()(left_available=True, right_available=True, left_error=True)
    controller._status_callback(status)
    controller._status_callback(status)
    qt_app.processEvents()

    assert received == [(True, "Left track motor error")]


def test_availability_timer_marks_controller_unavailable_after_timeout(qt_app, fake_node, caplog):
    controller = _wheel_controller_class()(fake_node)
    controller._left_motor_available = True
    controller._right_motor_available = True
    controller.set_available(True)
    controller._last_status_update_time = time.time() - 2.0

    controller._check_availability()

    assert controller.available is False
