"""Focused tests for the feature-root recording action boundary."""

from __future__ import annotations

from paint_controller.models.recording_actions import RecordingActions
from tests.fakes import FakeLogger


class FakeVideoStreamHandler:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.toggle_calls = 0
        self.base_toggle_calls = 0

    def toggleRecording(self) -> bool:
        self.toggle_calls += 1
        return self.result

    def toggleBaseRecording(self) -> bool:
        self.base_toggle_calls += 1
        return self.result


class FakeScreenRecorder:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.toggle_calls = 0

    def toggleRecording(self) -> bool:
        self.toggle_calls += 1
        return self.result


class FakeRosBagRecorder:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.toggle_calls = 0

    def toggleBagRecording(self) -> bool:
        self.toggle_calls += 1
        return self.result


def _build_actions(
    video_result: bool = True,
    screen_result: bool = True,
    bag_result: bool = True,
) -> tuple[RecordingActions, FakeVideoStreamHandler, FakeScreenRecorder, FakeRosBagRecorder, FakeLogger, list[tuple[bool, str]]]:
    video_stream_handler = FakeVideoStreamHandler(result=video_result)
    screen_recorder = FakeScreenRecorder(result=screen_result)
    ros_bag_recorder = FakeRosBagRecorder(result=bag_result)
    logger = FakeLogger()
    actions = RecordingActions(
        video_stream_handler=video_stream_handler,
        screen_recorder=screen_recorder,
        ros_bag_recorder=ros_bag_recorder,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))
    return actions, video_stream_handler, screen_recorder, ros_bag_recorder, logger, results


def test_recording_toggles_dispatch_to_backends() -> None:
    actions, video, screen, bag, logger, results = _build_actions()

    assert actions.toggleEndEffectorRecording() is True
    assert actions.toggleBaseRecording() is True
    assert actions.toggleScreenRecording() is True
    assert actions.toggleRosBagRecording() is True

    assert video.toggle_calls == 1
    assert video.base_toggle_calls == 1
    assert screen.toggle_calls == 1
    assert bag.toggle_calls == 1
    assert results[-1] == (True, "ROS bag recording requested")
    assert logger.records[-1].message == "ROS bag recording requested"


def test_backend_rejection_is_reported() -> None:
    actions, video, _screen, _bag, _logger, results = _build_actions(video_result=False)

    assert actions.toggleEndEffectorRecording() is False

    assert video.toggle_calls == 1
    assert results[-1] == (False, "EF camera recording was rejected by the backend")


def test_missing_controller_is_reported() -> None:
    logger = FakeLogger()
    actions = RecordingActions(
        video_stream_handler=None,
        screen_recorder=None,
        ros_bag_recorder=None,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))

    assert actions.toggleScreenRecording() is False

    assert results[-1] == (False, "Screen recording is unavailable")
    assert logger.records[-1].message == "Screen recording is unavailable"
