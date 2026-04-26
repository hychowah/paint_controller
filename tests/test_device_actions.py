"""Focused tests for the Python-owned hard device-action boundary."""

from __future__ import annotations

from paint_controller.handlers.device_actions import DeviceActionHandler
from tests.fakes import FakeLogger


class FakeTeensy:
    def __init__(self) -> None:
        self.relay_calls: list[bool] = []
        self.enable_calls: list[bool] = []
        self.home_top_calls: list[bool] = []
        self.home_arm_calls: list[bool] = []

    def setRelayEnabled(self, enabled: bool) -> None:
        self.relay_calls.append(enabled)

    def setEnabled(self, enabled: bool) -> None:
        self.enable_calls.append(enabled)

    def homeTopRail(self, home: bool) -> None:
        self.home_top_calls.append(home)

    def homeArm(self, home: bool) -> None:
        self.home_arm_calls.append(home)


class FakeWinch:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.enable_calls: list[bool] = []

    def setEnabled(self, enabled: bool) -> bool:
        self.enable_calls.append(enabled)
        return self.result


class FakeWheel:
    def __init__(self) -> None:
        self.enable_calls: list[bool] = []
        self.reset_calls = 0

    def setEnabled(self, enabled: bool) -> None:
        self.enable_calls.append(enabled)

    def resetWheelPosition(self) -> None:
        self.reset_calls += 1


def _build_handler(winch_result: bool = True) -> tuple[DeviceActionHandler, FakeTeensy, FakeWinch, FakeWheel, FakeLogger, list[tuple[bool, str]]]:
    teensy = FakeTeensy()
    winch = FakeWinch(result=winch_result)
    wheel = FakeWheel()
    logger = FakeLogger()
    handler = DeviceActionHandler(teensy=teensy, winch=winch, wheel=wheel, logger=logger)
    results: list[tuple[bool, str]] = []
    handler.operation_result.connect(lambda success, message: results.append((success, message)))
    return handler, teensy, winch, wheel, logger, results


def test_toggle_methods_invert_current_enabled_state() -> None:
    handler, teensy, winch, wheel, logger, results = _build_handler()

    assert handler.toggleTeensyRelay(True) is True
    assert handler.toggleTeensyEnable(False) is True
    assert handler.toggleWinchEnable(True) is True
    assert handler.toggleWheelEnable(False) is True

    assert teensy.relay_calls == [False]
    assert teensy.enable_calls == [True]
    assert winch.enable_calls == [False]
    assert wheel.enable_calls == [True]
    assert [message for _success, message in results] == [
        "Teensy relay requested",
        "Teensy enable requested",
        "Winch enable requested",
        "Wheel enable requested",
    ]
    assert logger.records[-1].message == "Wheel enable requested"


def test_reset_and_home_actions_dispatch_to_backend() -> None:
    handler, teensy, _winch, wheel, logger, results = _build_handler()

    assert handler.resetWheelPosition() is True
    assert handler.homeTopRail() is True
    assert handler.homeArm() is True

    assert wheel.reset_calls == 1
    assert teensy.home_top_calls == [True]
    assert teensy.home_arm_calls == [True]
    assert [message for _success, message in results] == [
        "Reset wheel position requested",
        "Home top rail requested",
        "Home arm rail requested",
    ]
    assert logger.records[-1].message == "Home arm rail requested"


def test_backend_rejection_is_reported() -> None:
    handler, _teensy, winch, _wheel, logger, results = _build_handler(winch_result=False)

    assert handler.toggleWinchEnable(False) is False

    assert winch.enable_calls == [True]
    assert results[-1] == (False, "Winch enable was rejected by the backend")
    assert logger.records[-1].message == "Winch enable was rejected by the backend"


def test_missing_controller_is_reported() -> None:
    logger = FakeLogger()
    handler = DeviceActionHandler(teensy=None, winch=None, wheel=None, logger=logger)
    results: list[tuple[bool, str]] = []
    handler.operation_result.connect(lambda success, message: results.append((success, message)))

    assert handler.resetWheelPosition() is False

    assert results[-1] == (False, "Reset wheel position is unavailable")
    assert logger.records[-1].message == "Reset wheel position is unavailable"