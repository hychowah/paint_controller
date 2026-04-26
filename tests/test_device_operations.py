"""Focused tests for the Python-owned device and operational side-effect boundary."""

from __future__ import annotations

from paint_controller.handlers.device_operations import DeviceOperationsHandler
from tests.fakes import FakeLogger


class FakeTeensy:
    def __init__(self) -> None:
        self.stability_calls: list[bool] = []
        self.yaw_calls: list[bool] = []
        self.auto_correction_calls: list[bool] = []
        self.leveling_calls: list[bool] = []
        self.roller_calls: list[bool] = []
        self.swing_calls: list[bool] = []
        self.led_calls: list[bool] = []
        self.lidar_power_calls: list[bool] = []

    def setStabilityEnabled(self, enabled: bool) -> None:
        self.stability_calls.append(enabled)

    def setYawEnabled(self, enabled: bool) -> None:
        self.yaw_calls.append(enabled)

    def setAutoCorrectonEnabled(self, enabled: bool) -> None:
        self.auto_correction_calls.append(enabled)

    def setSprayGunLevelingEnabled(self, enabled: bool) -> None:
        self.leveling_calls.append(enabled)

    def setRollerSteeringEnabled(self, enabled: bool) -> None:
        self.roller_calls.append(enabled)

    def setSwingDampingEnabled(self, enabled: bool) -> None:
        self.swing_calls.append(enabled)

    def setSprayGunLED(self, enabled: bool) -> None:
        self.led_calls.append(enabled)

    def setLidarPower(self, enabled: bool) -> None:
        self.lidar_power_calls.append(enabled)


class FakeWinch:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.load_detection_calls: list[bool] = []

    def setLoadDetectionEnabled(self, enabled: bool) -> bool:
        self.load_detection_calls.append(enabled)
        return self.result


class FakeVideoStreamHandler:
    def __init__(self) -> None:
        self.toggle_calls = 0
        self.base_toggle_calls = 0

    def toggleRecording(self) -> None:
        self.toggle_calls += 1

    def toggleBaseRecording(self) -> None:
        self.base_toggle_calls += 1


class FakeScreenRecorder:
    def __init__(self) -> None:
        self.toggle_calls = 0

    def toggleRecording(self) -> None:
        self.toggle_calls += 1


class FakeRosBagRecorder:
    def __init__(self) -> None:
        self.toggle_calls = 0

    def toggleBagRecording(self) -> None:
        self.toggle_calls += 1


class FakeHeartbeatHandler:
    def __init__(self) -> None:
        self.clear_calls = 0

    def clear_error_state(self) -> None:
        self.clear_calls += 1


class FakeAdminActionGate:
    def __init__(self) -> None:
        self.results: dict[str, tuple[bool, str]] = {}
        self.calls: list[str] = []

    def set_result(self, action_key: str, allowed: bool, reason: str = "") -> None:
        self.results[action_key] = (allowed, reason)

    def check_action(self, action_key: str) -> tuple[bool, str]:
        self.calls.append(action_key)
        return self.results.get(action_key, (True, ""))


def _build_handler(winch_result: bool = True) -> tuple[DeviceOperationsHandler, FakeTeensy, FakeWinch, FakeVideoStreamHandler, FakeScreenRecorder, FakeRosBagRecorder, FakeHeartbeatHandler, FakeAdminActionGate, FakeLogger, list[tuple[bool, str]]]:
    teensy = FakeTeensy()
    winch = FakeWinch(result=winch_result)
    video_stream_handler = FakeVideoStreamHandler()
    screen_recorder = FakeScreenRecorder()
    ros_bag_recorder = FakeRosBagRecorder()
    heartbeat_handler = FakeHeartbeatHandler()
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    handler = DeviceOperationsHandler(
        teensy=teensy,
        winch=winch,
        video_stream_handler=video_stream_handler,
        screen_recorder=screen_recorder,
        ros_bag_recorder=ros_bag_recorder,
        heartbeat_handler=heartbeat_handler,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    handler.operation_result.connect(lambda success, message: results.append((success, message)))
    return handler, teensy, winch, video_stream_handler, screen_recorder, ros_bag_recorder, heartbeat_handler, admin_action_gate, logger, results


def test_toggle_operations_dispatch_to_backend_and_invert_state() -> None:
    handler, teensy, winch, _video, _screen, _bag, _heartbeat, admin_action_gate, logger, results = _build_handler()

    assert handler.toggleLoadDetection(True) is True
    assert handler.toggleStability(False) is True
    assert handler.toggleYaw(True) is True
    assert handler.toggleAutoCorrection(False) is True
    assert handler.toggleSprayGunLeveling(True) is True
    assert handler.toggleRollerSteering(False) is True
    assert handler.toggleSwingDamping(True) is True
    assert handler.toggleSprayGunLed(False) is True
    assert handler.setLidarPower(True) is True

    assert winch.load_detection_calls == [False]
    assert teensy.stability_calls == [True]
    assert teensy.yaw_calls == [False]
    assert teensy.auto_correction_calls == [True]
    assert teensy.leveling_calls == [False]
    assert teensy.roller_calls == [True]
    assert teensy.swing_calls == [False]
    assert teensy.led_calls == [True]
    assert teensy.lidar_power_calls == [True]
    assert admin_action_gate.calls == ["winch.load_detection"]
    assert results[-1] == (True, "Lidar power requested")
    assert logger.records[-1].message == "Lidar power requested"


def test_recording_and_clear_error_operations_dispatch() -> None:
    handler, _teensy, _winch, video, screen, bag, heartbeat, _gate, logger, results = _build_handler()

    assert handler.toggleEndEffectorRecording() is True
    assert handler.toggleBaseRecording() is True
    assert handler.toggleScreenRecording() is True
    assert handler.toggleRosBagRecording() is True
    assert handler.clearErrors() is True

    assert video.toggle_calls == 1
    assert video.base_toggle_calls == 1
    assert screen.toggle_calls == 1
    assert bag.toggle_calls == 1
    assert heartbeat.clear_calls == 1
    assert results[-1] == (True, "Clear error states requested")
    assert logger.records[-1].message == "Clear error states requested"


def test_backend_rejection_is_reported_for_load_detection() -> None:
    handler, _teensy, winch, _video, _screen, _bag, _heartbeat, _gate, logger, results = _build_handler(winch_result=False)

    assert handler.toggleLoadDetection(False) is False

    assert winch.load_detection_calls == [True]
    assert results[-1] == (False, "Load detection was rejected by the backend")
    assert logger.records[-1].message == "Load detection was rejected by the backend"


def test_explicit_load_detection_request_dispatches_desired_state() -> None:
    handler, _teensy, winch, _video, _screen, _bag, _heartbeat, _gate, logger, results = _build_handler()

    assert handler.requestLoadDetectionEnabled(True) is True

    assert winch.load_detection_calls == [True]
    assert results[-1] == (True, "Load detection requested")
    assert logger.records[-1].message == "Load detection requested"


def test_gate_denial_blocks_load_detection_before_backend_call() -> None:
    handler, _teensy, winch, _video, _screen, _bag, _heartbeat, admin_action_gate, logger, results = _build_handler()
    admin_action_gate.set_result("winch.load_detection", False, "Load Detection Toggle is blocked while the controller heartbeat is in WARNING")

    assert handler.requestLoadDetectionEnabled(True) is False

    assert winch.load_detection_calls == []
    assert results[-1] == (False, "Load Detection Toggle is blocked while the controller heartbeat is in WARNING")
    assert logger.records[-1].message == "Load Detection Toggle is blocked while the controller heartbeat is in WARNING"