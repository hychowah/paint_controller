"""Focused tests for the feature-root Teensy action boundary."""

from __future__ import annotations

from paint_controller.models.teensy_actions import TeensyActions
from tests.fakes import FakeLogger


class FakeTeensy:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        # Intent members (mirror TeensyController)
        self.stability_enabled = False
        self.auto_correction_enabled = False
        self.spray_gun_leveling_enabled = False
        self.roller_steering_enabled = False
        self.swing_damping_enabled = False
        self.spray_gun_led_on = False
        # Firmware-echoed status flags
        self._status = {"yaw_enabled": False}
        self.stability_calls: list[bool] = []
        self.yaw_calls: list[bool] = []
        self.auto_correction_calls: list[bool] = []
        self.leveling_calls: list[bool] = []
        self.roller_calls: list[bool] = []
        self.swing_calls: list[bool] = []
        self.led_calls: list[bool] = []
        self.lidar_power_calls: list[bool] = []

    def get_status(self) -> dict:
        return dict(self._status)

    def setStabilityEnabled(self, enabled: bool) -> bool:
        self.stability_calls.append(enabled)
        self.stability_enabled = enabled
        return self.result

    def setYawEnabled(self, enabled: bool) -> bool:
        self.yaw_calls.append(enabled)
        self._status["yaw_enabled"] = enabled
        return self.result

    def setAutoCorrectionEnabled(self, enabled: bool) -> bool:
        self.auto_correction_calls.append(enabled)
        self.auto_correction_enabled = enabled
        return self.result

    def setSprayGunLevelingEnabled(self, enabled: bool) -> bool:
        self.leveling_calls.append(enabled)
        self.spray_gun_leveling_enabled = enabled
        return self.result

    def setRollerSteeringEnabled(self, enabled: bool) -> bool:
        self.roller_calls.append(enabled)
        self.roller_steering_enabled = enabled
        return self.result

    def setSwingDampingEnabled(self, enabled: bool) -> bool:
        self.swing_calls.append(enabled)
        self.swing_damping_enabled = enabled
        return self.result

    def setSprayGunLED(self, enabled: bool) -> bool:
        self.led_calls.append(enabled)
        self.spray_gun_led_on = enabled
        return self.result

    def setLidarPower(self, enabled: bool) -> bool:
        self.lidar_power_calls.append(enabled)
        return self.result


def _build_actions(result: bool = True) -> tuple[TeensyActions, FakeTeensy, FakeLogger, list[tuple[bool, str]]]:
    teensy = FakeTeensy(result=result)
    logger = FakeLogger()
    actions = TeensyActions(
        teensy=teensy,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))
    return actions, teensy, logger, results


def test_toggle_operations_invert_controller_state_and_dispatch() -> None:
    actions, teensy, logger, results = _build_actions()

    assert actions.toggleStability() is True
    assert actions.toggleYaw() is True
    assert actions.toggleAutoCorrection() is True
    assert actions.toggleSprayGunLeveling() is True
    assert actions.toggleRollerSteering() is True
    assert actions.toggleSwingDamping() is True
    assert actions.toggleSprayGunLed() is True
    assert actions.setLidarPower(True) is True

    assert teensy.stability_calls == [True]
    assert teensy.yaw_calls == [True]
    assert teensy.auto_correction_calls == [True]
    assert teensy.leveling_calls == [True]
    assert teensy.roller_calls == [True]
    assert teensy.swing_calls == [True]
    assert teensy.led_calls == [True]
    assert teensy.lidar_power_calls == [True]
    assert results[-1] == (True, "Lidar power requested")
    assert logger.records[-1].message == "Lidar power requested"


def test_toggles_negate_backend_state_not_caller_argument() -> None:
    actions, teensy, _logger, _results = _build_actions()
    teensy.stability_enabled = True
    teensy._status["yaw_enabled"] = True

    assert actions.toggleStability() is True
    assert actions.toggleYaw() is True

    assert teensy.stability_calls == [False]
    assert teensy.yaw_calls == [False]

    # State-driven inversion: a second toggle flips back
    assert actions.toggleStability() is True
    assert actions.toggleYaw() is True

    assert teensy.stability_calls == [False, True]
    assert teensy.yaw_calls == [False, True]


def test_backend_rejection_is_reported() -> None:
    actions, teensy, _logger, results = _build_actions(result=False)

    assert actions.toggleStability() is False

    assert teensy.stability_calls == [True]
    assert results[-1] == (False, "Stability controller was rejected by the backend")


def test_missing_controller_is_reported() -> None:
    logger = FakeLogger()
    actions = TeensyActions(
        teensy=None,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))

    assert actions.setLidarPower(True) is False

    assert results[-1] == (False, "Lidar power is unavailable")
    assert logger.records[-1].message == "Lidar power is unavailable"


def test_missing_controller_toggle_is_reported() -> None:
    logger = FakeLogger()
    actions = TeensyActions(
        teensy=None,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))

    assert actions.toggleStability() is False
    assert actions.toggleYaw() is False

    assert [message for _success, message in results] == [
        "Stability controller is unavailable",
        "Yaw control is unavailable",
    ]
