"""Direct tests for QmlContextComposer."""

from __future__ import annotations

from paint_controller.core import qml_context_composer
from paint_controller.core.qml_context_composer import QmlContextComposer
from tests.controller_factory_runtime_support import (
    _BaseTopViewServiceRecorder,
    _EngineRecorder,
    _HeartbeatHandlerRecorder,
    _LidarStatusRecorder,
    _QtBridgeRecorder,
    _RosBagRecorderRecorder,
    _ScreenRecorderRecorder,
    _SshControllerRecorder,
    _SystemMonitorRecorder,
    _TeensyControllerRecorder,
    _ValveStatusRecorder,
    _VideoHandlerRecorder,
    _WheelControllerRecorder,
    _WinchStatusRecorder,
)


def _make_runtime() -> object:
    """Return a minimal runtime-like object with the attributes composer needs."""
    runtime = type("Runtime", (), {})()
    runtime.state_store = object()
    runtime.qt_bridge = _QtBridgeRecorder()
    runtime.shell_state = object()
    runtime.shell_router = object()
    runtime.overlay_host = object()
    runtime.action_legality = object()
    runtime.settings_manager = object()
    runtime.video_stream_handler = _VideoHandlerRecorder()
    runtime.base_top_view_service = _BaseTopViewServiceRecorder()
    runtime.bundle = type(
        "Bundle",
        (),
        {
            "overlay_controller": object(),
            "workflow_runner": object(),
            "workflow_editor": object(),
            "manual_command_handler": object(),
            "warning_handler": object(),
            "recording_actions": object(),
            "teensy_actions": object(),
            "system_actions": object(),
            "wheel_actions": object(),
            "winch_actions": object(),
            "tuning_actions": object(),
            "base_top_view_actions": object(),
            "control_processor": _ControlProcessorRecorderForComposer(),
            "ssh_controller": _SshControllerRecorder(),
            "screen_recorder": _ScreenRecorderRecorder(),
            "ros_bag_recorder": _RosBagRecorderRecorder(),
            "system_monitor": _SystemMonitorRecorder(),
            "teensy_controller": _TeensyControllerRecorder(),
            "winch_controller": _WinchStatusRecorder(),
            "wheel_controller": _WheelControllerRecorder(),
            "esp32_valve_controller": _ValveStatusRecorder(),
            "lidar_controller": _LidarStatusRecorder(),
            "heartbeat_handler": _HeartbeatHandlerRecorder(),
        },
    )()
    return runtime


class _ControlProcessorRecorderForComposer:
    left_control_mode = "None"
    left_control_value = ""
    right_control_mode = "None"
    right_control_value = ""
    left_control_mode_display = ""
    right_control_mode_display = ""

    def __init__(self) -> None:
        self.left_control_mode_changed = _SignalRecorderForComposer()
        self.left_control_value_changed = _SignalRecorderForComposer()
        self.right_control_mode_changed = _SignalRecorderForComposer()
        self.right_control_value_changed = _SignalRecorderForComposer()
        self.left_control_mode_display_changed = _SignalRecorderForComposer()
        self.right_control_mode_display_changed = _SignalRecorderForComposer()


class _SignalRecorderForComposer:
    def __init__(self) -> None:
        self.connections: list[tuple[object, tuple]] = []

    def connect(self, callback, *args) -> None:
        self.connections.append((callback, args))


def test_expected_names_match_composed_keys() -> None:
    runtime = _make_runtime()
    properties = QmlContextComposer(runtime).compose()
    assert set(properties) == set(qml_context_composer._EXPECTED_CONTEXT_PROPERTY_NAMES)


def test_composer_creates_status_wrappers() -> None:
    runtime = _make_runtime()
    properties = QmlContextComposer(runtime).compose()

    assert properties["videoRuntime"] is not None
    assert properties["recordingStatus"] is not None
    assert properties["wheelStatus"] is not None
    assert properties["winchStatus"] is not None
    assert properties["teensyStatus"] is not None
    assert properties["valveStatus"] is not None
    assert properties["lidarStatus"] is not None
    assert properties["shellConnectivityStatus"] is not None
    assert properties["launcherAdmin"] is not None
    assert properties["baseTopViewStatus"] is not None
    assert properties["systemControlServices"] is not None


def test_composer_reuses_bundle_action_models() -> None:
    runtime = _make_runtime()
    properties = QmlContextComposer(runtime).compose()

    assert properties["recordingActions"] is runtime.bundle.recording_actions
    assert properties["teensyActions"] is runtime.bundle.teensy_actions
    assert properties["systemActions"] is runtime.bundle.system_actions
    assert properties["wheelActions"] is runtime.bundle.wheel_actions
    assert properties["winchActions"] is runtime.bundle.winch_actions
    assert properties["tuningActions"] is runtime.bundle.tuning_actions
    assert properties["baseTopViewActions"] is runtime.bundle.base_top_view_actions
    assert "deviceActionHandler" not in properties
    assert properties["overlayController"] is runtime.bundle.overlay_controller
    assert properties["warningHandler"] is runtime.bundle.warning_handler


def test_composer_reuses_runtime_level_objects() -> None:
    runtime = _make_runtime()
    properties = QmlContextComposer(runtime).compose()

    assert "stateStore" not in properties
    assert properties["qtBridge"] is runtime.qt_bridge
    assert properties["shellState"] is runtime.shell_state
    assert properties["shellRouter"] is runtime.shell_router
    assert properties["overlayHost"] is runtime.overlay_host
    assert properties["actionLegality"] is runtime.action_legality
    assert properties["settingsManager"] is runtime.settings_manager


def test_video_runtime_top_bar_reads_ssh_and_recorder() -> None:
    runtime = _make_runtime()
    properties = QmlContextComposer(runtime).compose()
    top_bar = properties["videoRuntime"].topBar

    assert top_bar.endEffectorConnected is True
    assert top_bar.baseConnected is True
    assert top_bar.systemBatteryPercent == 100
    assert top_bar.isRecording is False
    assert top_bar.recordingDuration == 120


def test_recording_status_reads_recorders() -> None:
    runtime = _make_runtime()
    properties = QmlContextComposer(runtime).compose()
    status = properties["recordingStatus"]

    assert status.endEffectorRecording is True
    assert status.baseRecording is False
    assert status.screenRecording is False
    assert status.screenRecordingDuration == 120
    assert status.screenFreeSpaceGb == 8.5
    assert status.rosBagRecording is True
    assert status.rosBagRecordingDuration == 33


def test_teensy_status_exposes_all_status_fields() -> None:
    runtime = _make_runtime()
    properties = QmlContextComposer(runtime).compose()
    teensy = properties["teensyStatus"]

    assert teensy.imuPitch == 1.5
    assert teensy.topRailPosition == 100.0
    assert teensy.leftPropPwm == 1200
    assert teensy.sprayGunTrigger is True


def test_compose_without_bundle_raises() -> None:
    runtime = _make_runtime()
    runtime.bundle = None
    try:
        QmlContextComposer(runtime).compose()
        assert False, "compose() should require a bundle"
    except RuntimeError as exc:
        assert "ControllerBundle is required" in str(exc)
