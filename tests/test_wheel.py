"""Tests for paint_controller.controllers.wheel.WheelController."""

from __future__ import annotations

import importlib
import time


def _wheel_controller_class():
    return importlib.import_module("paint_controller.controllers.wheel").WheelController


def _vehicle_status_class():
    return importlib.import_module("paint_interfaces.msg").VehicleStatus


def test_command_speed_publishes_unified_message(qt_app, fake_node):
    controller = _wheel_controller_class()(fake_node)

    assert controller.command_speed(120, -80) is True

    speed_msg = fake_node.publishers[0].published_messages[-1]
    assert speed_msg.left_rpm == 120
    assert speed_msg.right_rpm == -80


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


def test_status_callback_updates_availability_and_properties(qt_app, fake_node):
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

    assert controller.available is True
    assert controller.left_motor_available is True
    assert controller.right_motor_available is True
    assert controller.left_wheel_speed == 11.5
    assert controller.right_wheel_speed == -9.0
    assert controller.left_wheel_current == 4.2
    assert controller.right_wheel_current == 4.4
    assert controller.left_wheel_position == 150.0
    assert controller.right_wheel_position == 175.0


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

    assert received == [(True, "Left track motor error")]


def test_availability_timer_marks_controller_unavailable_after_timeout(qt_app, fake_node, caplog):
    controller = _wheel_controller_class()(fake_node)
    controller._left_motor_available = True
    controller._right_motor_available = True
    controller.set_available(True)
    controller._last_status_update_time = time.time() - 2.0

    controller._check_availability()

    assert controller.available is False
