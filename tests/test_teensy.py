"""Tests for paint_controller.controllers.teensy.TeensyController."""

from __future__ import annotations

import importlib


class FakeSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback) -> None:
        self._callbacks.append(callback)

    def emit(self, value) -> None:
        for callback in self._callbacks:
            callback(value)


class FakeSettingsManager:
    def __init__(self, thrust_force: float = -0.8, thrust_ramp_rate: float = 1.0) -> None:
        self._values = {
            "thrust_force": thrust_force,
            "thrust_ramp_rate": thrust_ramp_rate,
        }
        self.thrust_force_changed = FakeSignal()
        self.thrust_ramp_rate_changed = FakeSignal()

    def get(self, key: str, default=None):
        return self._values.get(key, default)


def _teensy_controller_class():
    return importlib.import_module("paint_controller.controllers.teensy").TeensyController


def _teensy_status_class():
    return importlib.import_module("paint_interfaces.msg").TeensyStatus


def test_status_callback_preserves_user_controlled_fields(qt_app, fake_node):
    controller = _teensy_controller_class()(fake_node)
    controller.setRelayEnabled(True)
    controller.setStabilityEnabled(True)
    controller.setRollerSteeringEnabled(True)
    controller.setSwingDampingEnabled(True)
    controller.setSprayGunLevelingEnabled(True)
    controller.setAutoCorrectionEnabled(True)
    controller.setLidarPower(True)

    status = _teensy_status_class()()
    status.runtime = 123000
    status.top_rail_position = 10.0
    status.arm_rail_position = 20.0
    status.left_prop_position = 250.0
    status.right_prop_position = 500.0
    status.orientation.z = 33.0
    status.yaw_command = 44.0

    controller._status_callback(status)
    current = controller.get_status()

    assert current["relay_enabled"] is True
    assert current["stability_enabled"] is True
    assert current["roller_steering_enabled"] is True
    assert current["swing_damping_enabled"] is True
    assert current["spray_gun_leveling_enabled"] is True
    assert current["auto_correction_enabled"] is True
    assert current["lidar_power"] is True
    assert current["left_prop_position"] == 2.5
    assert current["right_prop_position"] == 5.0
    assert current["imu_yaw"] == 33.0
    assert current["target_yaw"] == 44.0


def test_set_relay_enabled_updates_status_and_publishes(qt_app, fake_node):
    controller = _teensy_controller_class()(fake_node)

    controller.setRelayEnabled(True)

    published = controller.teensy_relay_pub.published_messages[-1]
    assert published.data is True
    assert controller.get_status()["relay_enabled"] is True


def test_status_changed_emits_defensive_snapshot(qt_app, fake_node):
    controller = _teensy_controller_class()(fake_node)
    emitted_statuses = []

    controller.status_changed.connect(emitted_statuses.append)

    controller.setRelayEnabled(True)

    assert emitted_statuses[-1]["relay_enabled"] is True
    emitted_statuses[-1]["relay_enabled"] = False
    assert controller.get_status()["relay_enabled"] is True


def test_get_all_status_returns_copy(qt_app, fake_node):
    controller = _teensy_controller_class()(fake_node)
    controller.setRelayEnabled(True)

    snapshot = controller.get_all_status()
    snapshot["relay_enabled"] = False

    assert controller.get_status()["relay_enabled"] is True


def test_spray_gun_leveling_emits_status_snapshot(qt_app, fake_node):
    controller = _teensy_controller_class()(fake_node)
    emitted_statuses = []

    controller.status_changed.connect(emitted_statuses.append)

    controller.setSprayGunLevelingEnabled(True)

    assert emitted_statuses[-1]["spray_gun_leveling_enabled"] is True


def test_set_lidar_power_updates_member_status_and_emits(qt_app, fake_node):
    controller = _teensy_controller_class()(fake_node)
    emitted_statuses = []

    controller.status_changed.connect(emitted_statuses.append)

    controller.setLidarPower(True)

    published = controller.ef_lidar_power_pub.published_messages[-1]
    assert published.data is True
    assert controller._lidar_power is True
    assert controller.get_status()["lidar_power"] is True
    assert emitted_statuses[-1]["lidar_power"] is True


def test_thrust_force_setting_change_clamps_value(qt_app, fake_node):
    settings = FakeSettingsManager(thrust_force=-0.4, thrust_ramp_rate=1.0)
    controller = _teensy_controller_class()(fake_node, settings_manager=settings)

    settings.thrust_force_changed.emit(2.5)

    assert controller.thrust_force == 1.0


def test_thrust_ramp_moves_toward_target_and_publishes(qt_app, fake_node):
    settings = FakeSettingsManager(thrust_force=-0.8, thrust_ramp_rate=2.0)
    controller = _teensy_controller_class()(fake_node, settings_manager=settings)
    forces = []
    controller.set_ef_force = lambda fx, fy: forces.append((fx, fy))

    controller.set_thrust_force_enabled(True)
    controller._update_thrust_ramp()
    controller._update_thrust_ramp()

    assert forces == [(0.0, -0.2), (0.0, -0.4)]
    assert controller._current_thrust_force == -0.4


def test_set_ef_force_publishes_twist_message(qt_app, fake_node):
    controller = _teensy_controller_class()(fake_node)

    controller.set_ef_force(1.5, -0.75)

    published = controller.stability_force_pub.published_messages[-1]
    assert published.linear.x == 1.5
    assert published.linear.y == -0.75
    assert published.linear.z == 0.0


def test_get_formatted_value_reads_status_via_locking_snapshot(qt_app, fake_node):
    controller = _teensy_controller_class()(fake_node)
    status = _teensy_status_class()()
    status.temperature = 23.456

    controller._status_callback(status)

    assert controller.get_formatted_value("temperature") == "23.5"
