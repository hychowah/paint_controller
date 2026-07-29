"""Direct tests for bounded AppRuntime seams and shutdown behavior."""

from __future__ import annotations

import importlib
import json

from paint_controller.core import qml_context_composer
from paint_controller.core.signal_wiring import SignalWiring
from tests.controller_factory_runtime_support import (
    _BaseTopViewServiceRecorder,
    _CleanupRecorder,
    _ControlProcessorRecorder,
    _EmergencyHandlerRecorder,
    _EngineRecorder,
    _HeartbeatHandlerRecorder,
    _InputHandlerRecorder,
    _LidarStatusRecorder,
    _QtBridgeRecorder,
    _RosBagRecorderRecorder,
    _runtime_without_bootstrap,
    _SafetyCoordinatorRecorder,
    _ScreenRecorderRecorder,
    _SignalRecorder,
    _SshControllerRecorder,
    _StatusTimerRecorder,
    _SteamDeckHandlerRecorder,
    _SystemMonitorRecorder,
    _TeensyControllerRecorder,
    _ValveStatusRecorder,
    _VideoHandlerRecorder,
    _WaitableRecorder,
    _WheelControllerRecorder,
    _WinchStatusRecorder,
)
from tests.fakes import FakeNode


class _SettingsManagerStub:
    """Public TD-050 port surface used by AppRuntime create_bundle tests."""

    def __init__(self) -> None:
        self._show_popup_fn = None
        self.admin_action_gate = None
        self.show_popup_set_calls: list[object] = []
        self.gate_set_calls: list[object] = []

    def set_show_popup_fn(self, fn) -> None:
        self.show_popup_set_calls.append(fn)
        self._show_popup_fn = fn

    def set_admin_action_gate(self, gate) -> None:
        self.gate_set_calls.append(gate)
        self.admin_action_gate = gate

    def require_ui_ports(self) -> None:
        if self._show_popup_fn is None:
            raise RuntimeError("SettingsManager.show_popup_fn not set")
        if self.admin_action_gate is None:
            raise RuntimeError("SettingsManager.admin_action_gate not set")


def test_app_runtime_create_bundle_and_register_context_properties(monkeypatch) -> None:
    module, runtime = _runtime_without_bootstrap(monkeypatch)

    runtime.node = FakeNode()
    runtime.settings_manager = _SettingsManagerStub()
    runtime.capability_catalog = object()
    runtime.state_store = type("StateStore", (), {"control_mode_changed": _SignalRecorder()})()
    runtime.steam_deck_handler = _SteamDeckHandlerRecorder()
    runtime.base_top_view_service = _BaseTopViewServiceRecorder()
    runtime.video_stream_handler = _VideoHandlerRecorder()
    runtime.qt_bridge = _QtBridgeRecorder()
    runtime.engine = _EngineRecorder()
    runtime.overlay_host = object()
    admin_gate = object()
    runtime.bundle = type(
        "Bundle",
        (),
        {
            "overlay_controller": object(),
            "workflow_runner": object(),
            "warning_handler": object(),
            "wheel_controller": _WheelControllerRecorder(),
            "winch_controller": _WinchStatusRecorder(),
            "wind_monitor": object(),
            "teensy_controller": _TeensyControllerRecorder(),
            "esp32_valve_controller": _ValveStatusRecorder(),
            "lidar_controller": _LidarStatusRecorder(),
            "heartbeat_handler": _HeartbeatHandlerRecorder(),
            "control_processor": _ControlProcessorRecorder(),
            "admin_action_gate": admin_gate,
            "manual_command_handler": object(),
            "recording_actions": object(),
            "teensy_actions": object(),
            "system_actions": object(),
            "wheel_actions": object(),
            "winch_actions": object(),
            "tuning_actions": object(),
            "base_top_view_actions": object(),
            "ssh_controller": _SshControllerRecorder(),
            "system_monitor": _SystemMonitorRecorder(),
            "screen_manager": object(),
            "screen_recorder": _ScreenRecorderRecorder(),
            "ros_bag_recorder": _RosBagRecorderRecorder(),
            "workflow_editor": object(),
            "input_handler": _InputHandlerRecorder(),
            "emergency_handler": _EmergencyHandlerRecorder(),
            "safety_coordinator": _SafetyCoordinatorRecorder(),
        },
    )()
    runtime.video_stream_handler = _VideoHandlerRecorder()

    create_calls: list[dict[str, object]] = []

    def fake_create_controllers(**kwargs):
        create_calls.append(kwargs)
        return runtime.bundle

    fake_factory = type("FactoryModule", (), {"create_controllers": staticmethod(fake_create_controllers)})
    monkeypatch.setitem(
        importlib.import_module("sys").modules, "paint_controller.core.controller_factory", fake_factory
    )

    runtime._create_controller_bundle()
    props = runtime._context_properties
    runtime._register_context_properties()
    SignalWiring(runtime._build_signal_wiring_ports(props["videoRuntime"])).wire()

    assert create_calls[0]["show_popup_fn"] == runtime.qt_bridge.show_popup
    assert create_calls[0]["close_popup_fn"] == runtime.qt_bridge.close_popup
    assert create_calls[0]["video_stream_handler"] is runtime.video_stream_handler
    assert create_calls[0]["base_top_view_service"] is runtime.base_top_view_service
    assert create_calls[0]["capability_catalog"] is runtime.capability_catalog
    assert runtime.qt_bridge.base_top_view_service is runtime.base_top_view_service
    assert runtime.qt_bridge.input_handler is runtime.bundle.input_handler
    assert runtime.settings_manager.gate_set_calls == [admin_gate]
    assert runtime.settings_manager.admin_action_gate is admin_gate
    assert runtime.action_legality is not None
    assert runtime.shell_router is not None
    # TD-047: façades live in the context map / bundle only — not AppRuntime mirrors.
    assert not hasattr(runtime, "wheel_status")
    assert not hasattr(runtime, "wheel_actions")
    assert not hasattr(runtime, "video_runtime")
    assert not hasattr(runtime, "recording_actions")
    assert props["systemControlServices"] is not None
    assert props["videoRuntime"] is not None
    assert props["recordingStatus"] is not None
    assert props["wheelStatus"] is not None
    assert props["winchStatus"] is not None
    assert props["teensyStatus"] is not None
    assert props["valveStatus"] is not None
    assert props["lidarStatus"] is not None
    assert props["baseTopViewStatus"] is not None
    assert props["baseTopViewActions"] is runtime.bundle.base_top_view_actions
    assert props["shellConnectivityStatus"] is not None
    assert props["launcherAdmin"] is not None
    engine_props = runtime.engine.context.properties
    assert engine_props["actionLegality"] is runtime.action_legality
    assert engine_props["systemControlServices"] is props["systemControlServices"]
    assert engine_props["videoRuntime"] is props["videoRuntime"]
    assert engine_props["recordingStatus"] is props["recordingStatus"]
    assert engine_props["wheelStatus"] is props["wheelStatus"]
    assert engine_props["winchStatus"] is props["winchStatus"]
    assert engine_props["teensyStatus"] is props["teensyStatus"]
    assert engine_props["valveStatus"] is props["valveStatus"]
    assert engine_props["lidarStatus"] is props["lidarStatus"]
    assert engine_props["shellConnectivityStatus"] is props["shellConnectivityStatus"]
    assert engine_props["launcherAdmin"] is props["launcherAdmin"]
    assert engine_props["wheelActions"] is runtime.bundle.wheel_actions
    assert engine_props["winchActions"] is runtime.bundle.winch_actions
    assert engine_props["tuningActions"] is runtime.bundle.tuning_actions
    assert engine_props["recordingActions"] is runtime.bundle.recording_actions
    assert engine_props["teensyActions"] is runtime.bundle.teensy_actions
    assert engine_props["systemActions"] is runtime.bundle.system_actions
    assert engine_props["baseTopViewActions"] is runtime.bundle.base_top_view_actions
    assert engine_props["baseTopViewStatus"] is props["baseTopViewStatus"]
    assert engine_props["shellRouter"] is runtime.shell_router
    assert "baseTopViewAdminHandler" not in engine_props
    assert "baseTopViewController" not in engine_props
    assert "deviceOperationsHandler" not in engine_props
    assert "teensyController" not in engine_props
    assert "esp32ValveController" not in engine_props
    assert "lidarController" not in engine_props
    assert "controlProcessor" not in engine_props
    assert "systemMonitor" not in engine_props
    assert "screenRecorder" not in engine_props
    assert "rosBagRecorder" not in engine_props
    assert "baseStreamHandler" not in engine_props
    assert "screenManager" not in engine_props
    assert "winchController" not in engine_props
    assert props["systemControlServices"].manualCommandHandler is runtime.bundle.manual_command_handler
    assert props["videoRuntime"].controls.leftMode == "None"
    assert props["videoRuntime"].topBar.systemBatteryPercent == 100
    assert props["videoRuntime"].topBar.endEffectorConnected is True
    assert props["videoRuntime"].topBar.baseConnected is True
    assert props["recordingStatus"].endEffectorRecording is True
    assert props["recordingStatus"].baseRecording is False
    assert props["recordingStatus"].screenRecording is False
    assert props["recordingStatus"].screenRecordingDuration == 120
    assert props["recordingStatus"].screenFreeSpaceGb == 8.5
    assert props["recordingStatus"].rosBagRecording is True
    assert props["recordingStatus"].rosBagRecordingDuration == 33
    assert props["recordingStatus"].rosBagCompressing is False
    assert props["recordingStatus"].rosBagStatusMessage == "Remote EF ready"
    assert props["wheelStatus"].available is True
    assert props["wheelStatus"].enabled is True
    assert props["wheelStatus"].leftMotorAvailable is True
    assert props["wheelStatus"].rightMotorAvailable is False
    assert props["wheelStatus"].leftWheelSpeed == 1.5
    assert props["wheelStatus"].rightWheelCurrent == 4.0
    assert props["wheelStatus"].leftWheelPosition == 125.0
    assert props["winchStatus"].available is True
    assert props["winchStatus"].loadDetectionEnabled is True
    assert props["winchStatus"].cableLength == 1200.0
    assert props["teensyStatus"].imuPitch == 1.5
    assert props["teensyStatus"].imuRoll == -0.5
    assert props["teensyStatus"].imuYaw == 3.0
    assert props["teensyStatus"].yawCommand == 5.0
    assert props["teensyStatus"].yawPidP == 0.1
    assert props["teensyStatus"].yawPidI == 0.2
    assert props["teensyStatus"].yawPidD == 0.3
    assert props["teensyStatus"].armExtensionDist == 320.0
    assert props["teensyStatus"].gimbalPitchMotorAngle == -4.5
    assert props["teensyStatus"].topRailPosition == 100.0
    assert props["teensyStatus"].topRailSpeed == 5.0
    assert props["teensyStatus"].topRailCurrent == 2.0
    assert props["teensyStatus"].armRailPosition == 200.0
    assert props["teensyStatus"].armRailSpeed == 3.0
    assert props["teensyStatus"].armRailCurrent == 40.0
    assert props["teensyStatus"].armSensorDist == 150.0
    assert props["teensyStatus"].leftPropPosition == 10.0
    assert props["teensyStatus"].rightPropPosition == 20.0
    assert props["teensyStatus"].leftPropPwm == 1200
    assert props["teensyStatus"].rightPropPwm == 1300
    assert props["teensyStatus"].sprayGunPitch == 45.0
    assert props["teensyStatus"].gimbalPitchMotorCurrent == 20.0
    assert props["teensyStatus"].gimbalPitchMotorTemp == 35.0
    assert props["teensyStatus"].gimbalRollMotorAngle == 5.0
    assert props["teensyStatus"].gimbalRollMotorCurrent == 15.0
    assert props["teensyStatus"].gimbalRollMotorTemp == 36.0
    assert props["teensyStatus"].sprayGunTrigger is True
    assert props["valveStatus"].valvePosition == 42.0
    assert props["valveStatus"].valveMotorConnected is True
    assert props["lidarStatus"].distance == 1.25
    assert props["lidarStatus"].angle == -3.5
    assert props["baseTopViewStatus"].enabled is True
    assert props["baseTopViewStatus"].editMode is False
    assert props["baseTopViewStatus"].zoom == 0.51
    assert props["baseTopViewStatus"].offsetX == 0.026
    assert props["baseTopViewStatus"].offsetY == 0.474
    assert props["baseTopViewStatus"].cropEnabled is True
    assert props["baseTopViewStatus"].cropWidthRatio == 0.9
    assert props["baseTopViewStatus"].cropCenterX == 0.5
    assert props["baseTopViewStatus"].k1 == -0.389
    assert props["baseTopViewStatus"].k2 == 0.142
    assert props["baseTopViewStatus"].k3 == 0.0
    assert props["baseTopViewStatus"].k4 == 0.0
    assert props["teensyStatus"].enabled is True
    assert props["teensyStatus"].relayOn is False
    assert props["teensyStatus"].loopTime == 450.0
    assert props["teensyStatus"].stabilityEnabled is True
    assert props["teensyStatus"].yawEnabled is True
    assert props["teensyStatus"].autoCorrectionEnabled is False
    assert props["teensyStatus"].sprayGunLevelingEnabled is True
    assert props["teensyStatus"].rollerSteeringEnabled is False
    assert props["teensyStatus"].swingDampingEnabled is True
    assert props["teensyStatus"].sprayGunLedOn is False
    assert props["shellConnectivityStatus"].winchAvailable is True
    assert props["shellConnectivityStatus"].wheelAvailable is True
    assert props["shellConnectivityStatus"].baseReachable is True
    assert props["shellConnectivityStatus"].endEffectorReachable is True
    assert props["shellConnectivityStatus"].endEffectorAvailable is True
    assert props["shellConnectivityStatus"].baseOnline is True
    assert props["shellConnectivityStatus"].baseStatus == 0x01
    assert props["shellConnectivityStatus"].endEffectorOnline is False
    assert props["shellConnectivityStatus"].endEffectorStatus == 0x02
    assert props["shellConnectivityStatus"].baseIpAddress == "10.0.0.2"
    assert props["shellConnectivityStatus"].endEffectorIpAddress == "10.0.0.3"
    launcher_admin = props["launcherAdmin"]
    assert json.loads(launcher_admin.getDeviceConfig("BASE")) == {
        "ip": "10.0.0.2",
        "port": "22",
        "username": "deck",
        "key_path": "~/.ssh/id_base",
    }
    assert launcher_admin.updateDeviceConfig("BASE", "10.0.0.20", "2200", "operator", "~/.ssh/id_new") is True
    launcher_admin.handleDeviceCommand("BASE", "Wheel", "start")
    assert runtime.bundle.ssh_controller.update_calls == [("BASE", "10.0.0.20", "2200", "operator", "~/.ssh/id_new")]
    assert runtime.bundle.ssh_controller.command_calls == [("BASE", "Wheel", "start")]
    assert "heartbeatHandler" not in engine_props
    assert "sshHandler" not in engine_props
    assert set(engine_props) == set(qml_context_composer._EXPECTED_CONTEXT_PROPERTY_NAMES)
    assert [button for button, _ in runtime.steam_deck_handler.callbacks] == [
        "up",
        "down",
        "left",
        "right",
        "r4",
        "l4",
        "menu",
        "switch",
        "l5",
        "r5",
        "dot",
        "a",
        "l1",
    ]


def test_setup_qml_engine_uses_public_set_show_popup_fn(monkeypatch, qt_app) -> None:
    """TD-050: popup inject lives in _setup_qml_engine — not create_bundle."""
    module, runtime = _runtime_without_bootstrap(monkeypatch)

    settings = _SettingsManagerStub()
    runtime.settings_manager = settings
    runtime.state_store = type(
        "StateStore",
        (),
        {
            "control_mode": "base",
            "display_message": "",
            "display_message_changed": None,
        },
    )()
    runtime.node = FakeNode()
    runtime.video_stream_handler = type(
        "Video",
        (),
        {
            "ef_image_provider": object(),
            "front_image_provider": object(),
            "rear_image_provider": object(),
        },
    )()
    runtime.base_top_view_service = type("BaseTop", (), {"image_provider": object()})()
    runtime.qml_dir = "/tmp"

    class FakeEngine:
        def addImageProvider(self, *_args, **_kwargs) -> None:
            pass

        def addImportPath(self, *_args, **_kwargs) -> None:
            pass

    class FakeBridge:
        def __init__(self, engine, state_store, logger=None, parent=None) -> None:
            self.engine = engine
            self.show_popup = object()

    monkeypatch.setattr(module, "QQmlApplicationEngine", FakeEngine)
    # Patch the real module object (namespace stubs break dotted monkeypatch paths).
    qt_bridge_mod = importlib.import_module("paint_controller.core.qt_bridge")
    monkeypatch.setattr(qt_bridge_mod, "QtBridge", FakeBridge)

    runtime._setup_qml_engine()

    assert len(settings.show_popup_set_calls) == 1
    assert settings.show_popup_set_calls[0] is runtime.qt_bridge.show_popup
    assert settings._show_popup_fn is runtime.qt_bridge.show_popup


def _settings_with_temp_path(monkeypatch, tmp_path, **kwargs):
    from pathlib import Path

    from paint_controller.core.settings import SettingsManager

    config_path = Path(tmp_path) / "config" / "settings.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)
    return SettingsManager(**kwargs)


def test_finalize_ui_ports_raises_when_settings_ports_missing(monkeypatch, tmp_path, qt_app) -> None:
    """TD-050: real SettingsManager.require_ui_ports fails until both ports set."""
    from paint_controller.core.qt_bridge import QtBridge

    _, runtime = _runtime_without_bootstrap(monkeypatch)
    runtime.settings_manager = _settings_with_temp_path(
        monkeypatch, tmp_path, show_popup_fn=None, admin_action_gate=None
    )
    runtime.qt_bridge = QtBridge(engine=object(), state_store=type("S", (), {"display_message_changed": None})())
    runtime.qt_bridge.set_base_top_view_service(object())
    runtime.qt_bridge.set_input_handler(object())

    try:
        runtime._finalize_ui_ports()
        raise AssertionError("expected RuntimeError for incomplete settings ports")
    except RuntimeError as exc:
        assert "show_popup_fn" in str(exc) or "admin_action_gate" in str(exc)


def test_finalize_ui_ports_raises_when_bridge_ports_missing(monkeypatch, tmp_path, qt_app) -> None:
    """TD-050: real QtBridge.require_ui_ports fails until both deps set."""
    from paint_controller.core.qt_bridge import QtBridge

    _, runtime = _runtime_without_bootstrap(monkeypatch)
    runtime.settings_manager = _settings_with_temp_path(
        monkeypatch,
        tmp_path,
        show_popup_fn=lambda *a: None,
        admin_action_gate=object(),
    )
    runtime.qt_bridge = QtBridge(engine=object(), state_store=type("S", (), {"display_message_changed": None})())

    try:
        runtime._finalize_ui_ports()
        raise AssertionError("expected RuntimeError for incomplete bridge ports")
    except RuntimeError as exc:
        assert "base_top_view_service" in str(exc) or "input_handler" in str(exc)


def test_finalize_ui_ports_passes_when_all_ports_set(monkeypatch, tmp_path, qt_app) -> None:
    from paint_controller.core.qt_bridge import QtBridge

    _, runtime = _runtime_without_bootstrap(monkeypatch)
    runtime.settings_manager = _settings_with_temp_path(
        monkeypatch,
        tmp_path,
        show_popup_fn=lambda *a: None,
        admin_action_gate=object(),
    )
    runtime.qt_bridge = QtBridge(engine=object(), state_store=type("S", (), {"display_message_changed": None})())
    runtime.qt_bridge.set_base_top_view_service(object())
    runtime.qt_bridge.set_input_handler(object())

    runtime._finalize_ui_ports()  # must not raise


def test_app_runtime_shutdown_cleans_resources_in_order(monkeypatch) -> None:
    module, runtime = _runtime_without_bootstrap(monkeypatch)
    call_log: list[str] = []

    status_timer = _StatusTimerRecorder()
    runtime.status_timer = status_timer
    engine_obj = object()
    app_obj = object()
    runtime.engine = engine_obj
    runtime.app = app_obj
    runtime.ros_thread = _WaitableRecorder("ros_thread", call_log)
    runtime.bundle = type("Bundle", (), {"cleanup": lambda self, logger: call_log.append("bundle.cleanup")})()
    runtime.base_top_view_service = _CleanupRecorder("base_top_view_service.cleanup", call_log)
    runtime.video_stream_handler = _CleanupRecorder("video_stream_handler.cleanup", call_log)
    runtime.steam_deck_handler = _CleanupRecorder("steam_deck_handler.cleanup", call_log)
    node = FakeNode()
    cleanup_calls: list[str] = []
    node.cleanup = lambda: cleanup_calls.append("node.cleanup")  # type: ignore[attr-defined]
    original_destroy_node = node.destroy_node
    node.destroy_node = lambda: (cleanup_calls.append("node.destroy_node"), original_destroy_node())[1]  # type: ignore[assignment]
    runtime.node = node
    runtime._shutdown_started = False

    teardown_calls: list[tuple[object, object]] = []
    monkeypatch.setattr(module, "teardown_qml_runtime", lambda engine, app, _log: teardown_calls.append((engine, app)))
    monkeypatch.setattr(module.rclpy, "ok", lambda: True)
    shutdown_calls: list[str] = []
    monkeypatch.setattr(module.rclpy, "shutdown", lambda: shutdown_calls.append("shutdown"))

    runtime.shutdown()

    assert status_timer.stopped is True
    assert status_timer.delete_later_called is True
    assert runtime.status_timer is None
    assert teardown_calls == [(engine_obj, app_obj)]
    assert call_log == [
        "ros_thread.request_shutdown",
        "ros_thread.wait(2000)",
        "bundle.cleanup",
        "base_top_view_service.cleanup",
        "video_stream_handler.cleanup",
        "steam_deck_handler.cleanup",
    ]
    assert cleanup_calls == ["node.cleanup", "node.destroy_node"]
    assert shutdown_calls == ["shutdown"]
    assert runtime.engine is None


def test_app_runtime_init_shuts_down_when_bootstrap_fails(monkeypatch) -> None:
    module = importlib.import_module("paint_controller.core.app_runtime")
    shutdown_calls: list[module.AppRuntime] = []

    def fake_bootstrap(self) -> None:
        self.ros_thread = object()
        raise RuntimeError("bootstrap failed")

    def fake_shutdown(self) -> None:
        shutdown_calls.append(self)

    monkeypatch.setattr(module.AppRuntime, "_bootstrap", fake_bootstrap)
    monkeypatch.setattr(module.AppRuntime, "shutdown", fake_shutdown)

    try:
        module.AppRuntime(argv=[])
    except RuntimeError as exc:
        assert str(exc) == "bootstrap failed"
    else:
        assert False, "AppRuntime constructor should re-raise bootstrap errors"

    assert len(shutdown_calls) == 1


def test_expected_context_properties_match_startup_smoke_fixture(monkeypatch, tmp_path) -> None:
    """Smoke fixture context objects must match AppRuntime's expected contract exactly."""
    from tests.startup_smoke_support import _context_objects

    context_objects = _context_objects(monkeypatch, tmp_path)
    expected = set(qml_context_composer._EXPECTED_CONTEXT_PROPERTY_NAMES)
    actual = set(context_objects)

    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)

    assert not missing, f"Startup smoke fixture missing expected context properties: {missing}"
    assert not unexpected, f"Startup smoke fixture has unexpected context properties: {unexpected}"
