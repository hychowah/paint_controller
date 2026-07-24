"""Focused tests for the feature-root Teensy action boundary."""

from __future__ import annotations

from paint_controller.models.teensy_actions import TeensyActions
from tests.fakes import FakeLogger


class FakeTeensy:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.stability_calls: list[bool] = []
        self.yaw_calls: list[bool] = []
        self.auto_correction_calls: list[bool] = []
        self.leveling_calls: list[bool] = []
        self.roller_calls: list[bool] = []
        self.swing_calls: list[bool] = []
        self.led_calls: list[bool] = []
        self.lidar_power_calls: list[bool] = []

    def setStabilityEnabled(self, enabled: bool) -> bool:
        self.stability_calls.append(enabled)
        return self.result

    def setYawEnabled(self, enabled: bool) -> bool:
        self.yaw_calls.append(enabled)
        return self.result

    def setAutoCorrectonEnabled(self, enabled: bool) -> bool:
        self.auto_correction_calls.append(enabled)
        return self.result

    def setSprayGunLevelingEnabled(self, enabled: bool) -> bool:
        self.leveling_calls.append(enabled)
        return self.result

    def setRollerSteeringEnabled(self, enabled: bool) -> bool:
        self.roller_calls.append(enabled)
        return self.result

    def setSwingDampingEnabled(self, enabled: bool) -> bool:
        self.swing_calls.append(enabled)
        return self.result

    def setSprayGunLED(self, enabled: bool) -> bool:
        self.led_calls.append(enabled)
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


def test_toggle_operations_invert_state_and_dispatch() -> None:
    actions, teensy, logger, results = _build_actions()

    assert actions.toggleStability(False) is True
    assert actions.toggleYaw(True) is True
    assert actions.toggleAutoCorrection(False) is True
    assert actions.toggleSprayGunLeveling(True) is True
    assert actions.toggleRollerSteering(False) is True
    assert actions.toggleSwingDamping(True) is True
    assert actions.toggleSprayGunLed(False) is True
    assert actions.setLidarPower(True) is True

    assert teensy.stability_calls == [True]
    assert teensy.yaw_calls == [False]
    assert teensy.auto_correction_calls == [True]
    assert teensy.leveling_calls == [False]
    assert teensy.roller_calls == [True]
    assert teensy.swing_calls == [False]
    assert teensy.led_calls == [True]
    assert teensy.lidar_power_calls == [True]
    assert results[-1] == (True, "Lidar power requested")
    assert logger.records[-1].message == "Lidar power requested"


def test_backend_rejection_is_reported() -> None:
    actions, teensy, _logger, results = _build_actions(result=False)

    assert actions.toggleStability(False) is False

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
