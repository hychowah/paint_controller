"""Direct tests for QmlContextComposer."""

from __future__ import annotations

from paint_controller.core import qml_context_composer
from paint_controller.core.qml_context_composer import QmlComposePorts, QmlContextComposer
from paint_controller.models.lidar_status import LidarStatus
from paint_controller.models.teensy_status import TeensyStatus
from paint_controller.models.valve_status import ValveStatus
from paint_controller.models.wheel_status import WheelStatus
from paint_controller.models.winch_status import WinchStatus
from tests.controller_factory_runtime_support import (
    _BaseTopViewServiceRecorder,
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


def _make_ports(**overrides) -> QmlComposePorts:
    """Return minimal QmlComposePorts for unit tests."""
    bundle = type(
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
    fields = {
        "bundle": bundle,
        "video_stream_handler": _VideoHandlerRecorder(),
        "base_top_view_service": _BaseTopViewServiceRecorder(),
        "qt_bridge": _QtBridgeRecorder(),
        "shell_state": object(),
        "shell_router": object(),
        "overlay_host": object(),
        "action_legality": object(),
        "settings_manager": object(),
    }
    fields.update(overrides)
    return QmlComposePorts(**fields)


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
    ports = _make_ports()
    properties = QmlContextComposer(ports).compose()
    assert set(properties) == set(qml_context_composer._EXPECTED_CONTEXT_PROPERTY_NAMES)


def test_composer_creates_status_wrappers() -> None:
    ports = _make_ports()
    properties = QmlContextComposer(ports).compose()

    assert properties["videoRuntime"] is not None
    assert properties["recordingStatus"] is not None
    assert isinstance(properties["wheelStatus"], WheelStatus)
    assert properties["wheelStatus"].leftWheelSpeed == 1.5
    assert isinstance(properties["winchStatus"], WinchStatus)
    assert properties["winchStatus"].cableLength == 1200.0
    assert properties["winchStatus"].available is True
    assert isinstance(properties["teensyStatus"], TeensyStatus)
    assert properties["teensyStatus"].imuPitch == 1.5
    assert isinstance(properties["valveStatus"], ValveStatus)
    assert properties["valveStatus"].valvePosition == 42.0
    assert isinstance(properties["lidarStatus"], LidarStatus)
    assert properties["lidarStatus"].distance == 1.25
    assert properties["shellConnectivityStatus"] is not None
    assert properties["launcherAdmin"] is not None
    assert properties["baseTopViewStatus"] is not None
    assert properties["systemControlServices"] is not None


def test_composer_reuses_bundle_action_models() -> None:
    ports = _make_ports()
    properties = QmlContextComposer(ports).compose()

    assert properties["recordingActions"] is ports.bundle.recording_actions
    assert properties["teensyActions"] is ports.bundle.teensy_actions
    assert properties["systemActions"] is ports.bundle.system_actions
    assert properties["wheelActions"] is ports.bundle.wheel_actions
    assert properties["winchActions"] is ports.bundle.winch_actions
    assert properties["tuningActions"] is ports.bundle.tuning_actions
    assert properties["baseTopViewActions"] is ports.bundle.base_top_view_actions
    assert "deviceActionHandler" not in properties
    assert properties["overlayController"] is ports.bundle.overlay_controller
    assert properties["warningHandler"] is ports.bundle.warning_handler


def test_composer_reuses_port_level_objects() -> None:
    ports = _make_ports()
    properties = QmlContextComposer(ports).compose()

    assert "stateStore" not in properties
    assert properties["qtBridge"] is ports.qt_bridge
    assert properties["shellState"] is ports.shell_state
    assert properties["shellRouter"] is ports.shell_router
    assert properties["overlayHost"] is ports.overlay_host
    assert properties["actionLegality"] is ports.action_legality
    assert properties["settingsManager"] is ports.settings_manager


def test_video_runtime_top_bar_reads_ssh_and_recorder() -> None:
    ports = _make_ports()
    properties = QmlContextComposer(ports).compose()
    top_bar = properties["videoRuntime"].topBar

    assert top_bar.endEffectorConnected is True
    assert top_bar.baseConnected is True
    assert top_bar.systemBatteryPercent == 100
    assert top_bar.isRecording is False
    assert top_bar.recordingDuration == 120


def test_recording_status_reads_recorders() -> None:
    ports = _make_ports()
    properties = QmlContextComposer(ports).compose()
    status = properties["recordingStatus"]

    assert status.endEffectorRecording is True
    assert status.baseRecording is False
    assert status.screenRecording is False
    assert status.screenRecordingDuration == 120
    assert status.screenFreeSpaceGb == 8.5
    assert status.rosBagRecording is True
    assert status.rosBagRecordingDuration == 33


def test_teensy_status_exposes_all_status_fields() -> None:
    ports = _make_ports()
    properties = QmlContextComposer(ports).compose()
    teensy = properties["teensyStatus"]

    assert teensy.imuPitch == 1.5
    assert teensy.topRailPosition == 100.0
    assert teensy.leftPropPwm == 1200
    assert teensy.sprayGunTrigger is True


def test_compose_without_bundle_raises() -> None:
    ports = _make_ports(bundle=None)
    try:
        QmlContextComposer(ports).compose()
        assert False, "compose() should require a bundle"
    except RuntimeError as exc:
        assert "ControllerBundle is required" in str(exc)
