"""Tests for paint_controller.controllers.winch.WinchController."""

from __future__ import annotations

import importlib

from tests.fakes import FakeNode, FakeRosBus


class FakeSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback) -> None:
        self._callbacks.append(callback)

    def emit(self, value) -> None:
        for callback in self._callbacks:
            callback(value)


class FakeSettingsManager:
    def __init__(self, initial_value: float) -> None:
        self._value = initial_value
        self.winch_max_speed_mmps_changed = FakeSignal()

    def get(self, key: str):
        if key == "winch_max_speed_mmps":
            return self._value
        return None


def _winch_controller_class():
    return importlib.import_module("paint_controller.controllers.winch").WinchController


def test_speed_commands_rejected_when_unavailable(qt_app, fake_node):
    controller = _winch_controller_class()(fake_node)

    assert controller.command_speed_rpm(123.0) is False
    assert controller.command_speed_mmps(123.0) is False
    assert fake_node.publishers[0].published_messages == []
    assert fake_node.publishers[1].published_messages == []


def test_command_bus_defers_continuous_speed_until_pump(qt_app, fake_node):
    """TD-054: winch continuous speed commands enqueue until RosCommandBus.pump()."""
    from paint_controller.core.ros_io import RosCommandBus

    bus = RosCommandBus()
    controller = _winch_controller_class()(fake_node, command_bus=bus)
    controller.set_available(True)
    rpm_pub = fake_node.publishers[0]

    assert controller.command_speed_rpm(100.0) is True
    assert rpm_pub.published_messages == []
    assert bus.pending_counts()[1] == 1

    assert bus.pump() == 1
    assert len(rpm_pub.published_messages) == 1


def test_move_commands_guard_when_unavailable(qt_app, fake_node):
    controller = _winch_controller_class()(fake_node)

    assert controller.move_increment(100, 50) is False
    assert controller.move_increment_with_accel(100, 50, 20) is False
    assert controller.move_absolute(500, 70) is False
    assert controller.move_absolute_with_accel(500, 70, 25) is False

    warning_messages = [record.message for record in fake_node.get_logger().records if record.level == "warning"]
    assert warning_messages == [
        "Cannot move increment: Winch not available",
        "Cannot move increment: Winch not available",
        "Cannot move absolute: Winch not available",
        "Cannot move absolute: Winch not available",
    ]


def test_enable_and_load_detection_guard_when_unavailable(qt_app, fake_node):
    controller = _winch_controller_class()(fake_node)

    assert controller.set_load_detection_mode(True) is False
    assert controller.setEnabled(True) is False

    assert fake_node.publishers[2].published_messages == []
    assert fake_node.publishers[5].published_messages == []

    warning_messages = [record.message for record in fake_node.get_logger().records if record.level == "warning"]
    assert warning_messages == [
        "Cannot set load detection: Winch not available",
        "Cannot enable winch: Winch not available",
    ]


def test_speed_commands_clamp_to_max_speed(qt_app, fake_node):
    controller = _winch_controller_class()(fake_node)
    controller.set_available(True)

    assert controller.command_speed_rpm(999.0) is True
    assert controller.command_speed_mmps(-999.0) is True

    rpm_msg = fake_node.publishers[0].published_messages[-1]
    mmps_msg = fake_node.publishers[1].published_messages[-1]
    assert rpm_msg.data == 400.0
    assert mmps_msg.data == -400.0


def test_enable_command_publishes_when_available(qt_app, fake_node):
    controller = _winch_controller_class()(fake_node)
    controller.set_available(True)

    controller.setEnabled(True)

    enable_msg = fake_node.publishers[2].published_messages[-1]
    assert enable_msg.data is True


def test_settings_manager_initial_value_and_updates_change_clamp(qt_app, fake_node):
    settings = FakeSettingsManager(initial_value=125.0)
    controller = _winch_controller_class()(fake_node, settings_manager=settings)
    controller.set_available(True)

    controller.command_speed_mmps(300.0)
    first_msg = fake_node.publishers[1].published_messages[-1]
    assert first_msg.data == 125.0

    settings.winch_max_speed_mmps_changed.emit(75.0)
    controller.command_speed_mmps(300.0)
    second_msg = fake_node.publishers[1].published_messages[-1]
    assert second_msg.data == 75.0


def test_move_increment_publishes_message_when_available(qt_app, fake_node):
    controller = _winch_controller_class()(fake_node)
    controller.set_available(True)

    assert controller.move_increment(250, 60) is True

    move_msg = fake_node.publishers[3].published_messages[-1]
    assert move_msg.length_mm == 250
    assert move_msg.speed_mm_s == 60
    assert move_msg.acceleration_rpm_s == 30


def test_speed_command_reaches_subscriber_over_fake_ros_bus(qt_app):
    bus = FakeRosBus()
    publisher_node = FakeNode(bus=bus)
    subscriber_node = FakeNode(bus=bus)
    controller = _winch_controller_class()(publisher_node)
    controller.set_available(True)
    received = []

    subscriber_node.create_subscription(
        object,
        "winch/move/speed/mmps/cmd",
        lambda message: received.append(message.data),
        1,
    )

    assert controller.command_speed_mmps(150.0) is True

    assert received == [150.0]


def test_status_callback_does_not_mutate_until_events(qt_app, fake_node):
    """TD-056 affinity: ROS callback posts only; apply after processEvents."""
    import time

    from paint_controller.controllers.winch import WinchStatusSnapshot

    controller = _winch_controller_class()(fake_node)
    snap = WinchStatusSnapshot(
        recv_mono=time.time(),
        enabled=True,
        cable_length=12.5,
        cable_speed=1.0,
        winch_torque=2.0,
        motor_temperature=40.0,
        motor_voltage=48.0,
        motor_brake=False,
        load_detection_mode=True,
        unusual_load_detected=False,
    )
    # Direct apply path (unit).
    controller._apply_status_snapshot(snap)
    assert controller.available is True
    assert controller.cable_length == 12.5
    assert controller.enabled is True

    # Callback path: no sync mutation of teleop-visible fields.
    controller2 = _winch_controller_class()(fake_node)
    # Build a minimal fake message-like object with attributes used by snapshot.
    class _Msg:
        enabled = True
        cable_length = 99.0
        cable_speed = 0.0
        winch_torque = 0.0
        motor_temperature = 0.0
        motor_voltage = 0.0
        motor_brake = True
        load_detection_mode = False
        unusual_load_detected = False

    controller2._status_callback(_Msg())
    assert controller2.available is False
    assert controller2.cable_length == 0.0
    qt_app.processEvents()
    assert controller2.available is True
    assert controller2.cable_length == 99.0


def test_status_callback_from_worker_thread_defers_apply(qt_app, fake_node):
    """Worker-thread ROS callback posts only; cable_length applies after main processEvents."""
    import threading

    controller = _winch_controller_class()(fake_node)

    class _Msg:
        enabled = True
        cable_length = 42.0
        cable_speed = 0.5
        winch_torque = 1.0
        motor_temperature = 30.0
        motor_voltage = 48.0
        motor_brake = False
        load_detection_mode = True
        unusual_load_detected = False

    errors: list[BaseException] = []
    main_tid = threading.get_ident()
    apply_tids: list[int] = []
    orig_apply = controller._telemetry._apply_fn

    def tracking_apply(snap):
        apply_tids.append(threading.get_ident())
        return orig_apply(snap)

    controller._telemetry._apply_fn = tracking_apply

    def worker() -> None:
        try:
            controller._status_callback(_Msg())
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=worker, name="winch-status-worker")
    thread.start()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert errors == []

    assert controller.available is False
    assert controller.cable_length == 0.0
    assert apply_tids == []

    qt_app.processEvents()

    assert controller.available is True
    assert controller.cable_length == 42.0
    assert apply_tids == [main_tid], f"apply must run on main thread, got {apply_tids}"
