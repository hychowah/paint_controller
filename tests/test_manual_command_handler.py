"""Focused tests for the Python-owned manual command boundary."""

from __future__ import annotations

from paint_controller.handlers.manual_commands import ManualCommandHandler
from tests.fakes import FakeLogger


class FakeTeensy:
    def __init__(self) -> None:
        self.spray_angle_calls: list[tuple[float, float]] = []
        self.force_calls: list[tuple[float, float]] = []
        self.extend_calls: list[int] = []
        self.frequency_tap_calls: list[tuple[float, float]] = []
        self.tap_once_calls: list[float] = []

    def setSprayGunPitchAngle(self, angle: float, speed: float) -> None:
        self.spray_angle_calls.append((angle, speed))

    def set_ef_force(self, fx: float, fy: float) -> None:
        self.force_calls.append((fx, fy))

    def extendArm(self, length: int) -> None:
        self.extend_calls.append(length)

    def startTapFreq(self, power: float, period: float) -> None:
        self.frequency_tap_calls.append((power, period))

    def tapOnce(self, power: float) -> None:
        self.tap_once_calls.append(power)


class FakeWinch:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.move_calls: list[tuple[int, int, int]] = []
        self.absolute_calls: list[tuple[int, int, int]] = []

    def move_increment_with_accel(self, distance: int, speed: int, acceleration: int) -> bool:
        self.move_calls.append((distance, speed, acceleration))
        return self.result

    def move_absolute_with_accel(self, length: int, speed: int, acceleration: int = 30) -> bool:
        self.absolute_calls.append((length, speed, acceleration))
        return self.result

    def get_cable_length(self) -> float:
        return 0.0


def _build_handler(
    winch_result: bool = True,
) -> tuple[ManualCommandHandler, FakeTeensy, FakeWinch, FakeLogger, list[tuple[bool, str]]]:
    teensy = FakeTeensy()
    winch = FakeWinch(result=winch_result)
    logger = FakeLogger()
    handler = ManualCommandHandler(teensy=teensy, winch=winch, logger=logger)
    results: list[tuple[bool, str]] = []
    handler.operation_result.connect(lambda success, message: results.append((success, message)))
    return handler, teensy, winch, logger, results


def test_is_command_supported_distinguishes_live_and_unimplemented_commands() -> None:
    handler, _teensy, _winch, _logger, _results = _build_handler()

    assert handler.isCommandSupported("Demo") is True
    assert handler.isCommandSupported("Move to Position") is False


def test_execute_set_spray_gun_angle_coerces_float_parameters() -> None:
    handler, teensy, _winch, logger, results = _build_handler()

    success = handler.executeCommand("Set Spray Gun Angle", {"Angle": "12.5", "Speed": "3.0"})

    assert success is True
    assert teensy.spray_angle_calls == [(12.5, 3.0)]
    assert results[-1] == (True, "Command sent: Set Spray Gun Angle")
    assert logger.records[-1].message == "Command sent: Set Spray Gun Angle"


def test_execute_demo_uses_application_demo_sequence_not_teensy_method() -> None:
    """TD-055: Demo orchestrates teensy + winch via demo_sequence (not Teensy.demoAction)."""
    handler, teensy, winch, _logger, _results = _build_handler()

    success = handler.executeCommand(
        "Demo",
        {
            "Gimbal Angle": "10.0",
            "Gimbal Speed": "2.5",
            "Cable Length": "100.0",
            "Cable Speed": "50.0",
            "Force Y": "8.5",
        },
    )

    assert success is True
    assert teensy.spray_angle_calls == [(10.0, 2.5)]
    assert winch.absolute_calls == [(100, 50, 30)]
    assert teensy.force_calls == [(0.0, 8.5)]
    assert not hasattr(teensy, "demoAction") or not callable(getattr(type(teensy), "demoAction", None))


def test_execute_winch_control_accepts_integer_like_strings() -> None:
    handler, _teensy, winch, _logger, _results = _build_handler()

    success = handler.executeCommand(
        "Winch Control",
        {"Distance": "120.0", "Speed": "450", "Acceleration": "30.0"},
    )

    assert success is True
    assert winch.move_calls == [(120, 450, 30)]


def test_execute_command_rejects_missing_parameter() -> None:
    handler, teensy, _winch, logger, results = _build_handler()

    success = handler.executeCommand("Frequency Tap", {"Power": "1.0"})

    assert success is False
    assert teensy.frequency_tap_calls == []
    assert results[-1] == (False, "Missing parameter: Period")
    assert logger.records[-1].message == "Missing parameter: Period"


def test_execute_command_rejects_unsupported_command() -> None:
    handler, teensy, winch, logger, results = _build_handler()

    success = handler.executeCommand("Move to Position", {"X Position": "1.0"})

    assert success is False
    assert teensy.spray_angle_calls == []
    assert winch.move_calls == []
    assert results[-1] == (False, "Command 'Move to Position' is not available yet")
    assert logger.records[-1].message == "Command 'Move to Position' is not available yet"


def test_execute_command_reports_backend_rejection() -> None:
    handler, _teensy, winch, logger, results = _build_handler(winch_result=False)

    success = handler.executeCommand(
        "Winch Control",
        {"Distance": "120", "Speed": "450", "Acceleration": "30"},
    )

    assert success is False
    assert winch.move_calls == [(120, 450, 30)]
    assert results[-1] == (False, "Command 'Winch Control' was rejected by the backend")
    assert logger.records[-1].message == "Command 'Winch Control' was rejected by the backend"
