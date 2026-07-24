"""Direct tests for bounded AppRuntime seams and shutdown behavior."""

from __future__ import annotations

import importlib
import json

from tests.controller_factory_runtime_support import (
    FakeNode,
    _CleanupRecorder,
    _ControlProcessorRecorder,
    _EngineRecorder,
    _EmergencyHandlerRecorder,
    _HeartbeatHandlerRecorder,
    _InputHandlerRecorder,
    _LidarStatusRecorder,
    _QtBridgeRecorder,
    _RosBagRecorderRecorder,
    _ScreenRecorderRecorder,
    _SafetyCoordinatorRecorder,
    _ScreenRecorderRecorder,
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
    _runtime_without_bootstrap,
)


def test_app_runtime_create_bundle_and_register_context_properties(monkeypatch) -> None:
    module, runtime = _runtime_without_bootstrap(monkeypatch)

    runtime.node = FakeNode()
    runtime.settings_manager = type("Settings", (), {"_show_popup_fn": None})()
    runtime.capability_catalog = object()
    runtime.state_store = object()
    runtime.steam_deck_handler = _SteamDeckHandlerRecorder()
    runtime.base_top_view_service = object()
    runtime.video_stream_handler = _VideoHandlerRecorder()
    runtime.qt_bridge = _QtBridgeRecorder()
    runtime.engine = _EngineRecorder()
    runtime.overlay_host = object()
    runtime.bundle = type(
        "Bundle",
        (),
        {
            "overlay_controller": object(),
            "workflow_runner": object(),
            "warning_handler": object(),
            "wheel_controller": _WheelControllerRecorder(),
            "winch_controller": object(),
            "wind_monitor": object(),
            "teensy_controller": object(),
            "esp32_valve_controller": _ValveStatusRecorder(),
            "lidar_controller": _LidarStatusRecorder(),
            "heartbeat_handler": _HeartbeatHandlerRecorder(),
            "control_processor": _ControlProcessorRecorder(),
            "admin_action_gate": object(),
            "manual_command_handler": object(),
            "device_action_handler": object(),
            "device_operations_handler": object(),
            "wheel_actions": object(),
            "winch_actions": object(),
            "tuning_actions": object(),
            "base_top_view_admin_handler": object(),
            "ssh_controller": _SshControllerRecorder(),
            "system_monitor": _SystemMonitorRecorder(),
            "screen_manager": object(),
            "screen_recorder": _ScreenRecorderRecorder(),
            "ros_bag_recorder": _RosBagRecorderRecorder(),
            "workflow_editor": object(),
            "input_handler": _InputHandlerRecorder(),
            "emergency_handler": _EmergencyHandlerRecorder(),
            "safety_coordinator": _SafetyCoordinatorRecorder(),
            "teensy_controller": _TeensyControllerRecorder(),
            "winch_controller": _WinchStatusRecorder(),
        },
    )()
    runtime.video_stream_handler = _VideoHandlerRecorder()

    create_calls: list[dict[str, object]] = []

    def fake_create_controllers(**kwargs):
        create_calls.append(kwargs)
        return runtime.bundle

    fake_factory = type("FactoryModule", (), {"create_controllers": staticmethod(fake_create_controllers)})
    monkeypatch.setitem(importlib.import_module("sys").modules, "paint_controller.core.controller_factory", fake_factory)

    runtime._create_controller_bundle()
    runtime._register_context_properties()
    runtime._wire_steam_deck_callbacks()

    assert create_calls[0]["show_popup_fn"] == runtime.qt_bridge.show_popup
    assert create_calls[0]["close_popup_fn"] == runtime.qt_bridge.close_popup
    assert create_calls[0]["video_stream_handler"] is runtime.video_stream_handler
    assert create_calls[0]["base_top_view_service"] is runtime.base_top_view_service
    assert create_calls[0]["capability_catalog"] is runtime.capability_catalog
    assert runtime.qt_bridge.base_top_view_service is runtime.base_top_view_service
    assert runtime.qt_bridge.input_handler is runtime.bundle.input_handler
    assert runtime.action_legality is not None
    assert runtime.system_control_services is not None
    assert runtime.video_runtime is not None
    assert runtime.recording_status is not None
    assert runtime.wheel_status is not None
    assert runtime.winch_status is not None
    assert runtime.teensy_status is not None
    assert runtime.valve_status is not None
    assert runtime.lidar_status is not None
    assert runtime.shell_connectivity_status is not None
    assert runtime.launcher_admin is not None
    assert runtime.engine.context.properties["actionLegality"] is runtime.action_legality
    assert runtime.engine.context.properties["systemControlServices"] is runtime.system_control_services
    assert runtime.engine.context.properties["videoRuntime"] is runtime.video_runtime
    assert runtime.engine.context.properties["recordingStatus"] is runtime.recording_status
    assert runtime.engine.context.properties["wheelStatus"] is runtime.wheel_status
    assert runtime.engine.context.properties["winchStatus"] is runtime.winch_status
    assert runtime.engine.context.properties["teensyStatus"] is runtime.teensy_status
    assert runtime.engine.context.properties["valveStatus"] is runtime.valve_status
    assert runtime.engine.context.properties["lidarStatus"] is runtime.lidar_status
    assert runtime.engine.context.properties["shellConnectivityStatus"] is runtime.shell_connectivity_status
    assert runtime.engine.context.properties["launcherAdmin"] is runtime.launcher_admin
    assert runtime.engine.context.properties["wheelActions"] is runtime.bundle.wheel_actions
    assert runtime.engine.context.properties["winchActions"] is runtime.bundle.winch_actions
    assert runtime.engine.context.properties["tuningActions"] is runtime.bundle.tuning_actions
    assert runtime.system_control_services.manualCommandHandler is runtime.bundle.manual_command_handler
    assert runtime.video_runtime.controls.leftMode == "None"
    assert runtime.video_runtime.topBar.systemBatteryPercent == 100
    assert runtime.video_runtime.topBar.endEffectorConnected is True
    assert runtime.video_runtime.topBar.baseConnected is True
    assert runtime.recording_status.endEffectorRecording is True
    assert runtime.recording_status.baseRecording is False
    assert runtime.recording_status.screenRecording is False
    assert runtime.recording_status.screenRecordingDuration == 120
    assert runtime.recording_status.screenFreeSpaceGb == 8.5
    assert runtime.recording_status.rosBagRecording is True
    assert runtime.recording_status.rosBagRecordingDuration == 33
    assert runtime.recording_status.rosBagCompressing is False
    assert runtime.recording_status.rosBagStatusMessage == "Remote EF ready"
    assert runtime.wheel_status.available is True
    assert runtime.wheel_status.enabled is True
    assert runtime.wheel_status.leftMotorAvailable is True
    assert runtime.wheel_status.rightMotorAvailable is False
    assert runtime.wheel_status.leftWheelSpeed == 1.5
    assert runtime.wheel_status.rightWheelCurrent == 4.0
    assert runtime.wheel_status.leftWheelPosition == 125.0
    assert runtime.winch_status.available is True
    assert runtime.winch_status.loadDetectionEnabled is True
    assert runtime.winch_status.cableLength == 1200.0
    assert runtime.teensy_status.imuPitch == 1.5
    assert runtime.teensy_status.imuRoll == -0.5
    assert runtime.teensy_status.imuYaw == 3.0
    assert runtime.teensy_status.yawCommand == 5.0
    assert runtime.teensy_status.yawPidP == 0.1
    assert runtime.teensy_status.yawPidI == 0.2
    assert runtime.teensy_status.yawPidD == 0.3
    assert runtime.teensy_status.armExtensionDist == 320.0
    assert runtime.teensy_status.gimbalPitchMotorAngle == -4.5
    assert runtime.valve_status.valvePosition == 42.0
    assert runtime.valve_status.valveMotorConnected is True
    assert runtime.lidar_status.distance == 1.25
    assert runtime.lidar_status.angle == -3.5
    assert runtime.teensy_status.enabled is True
    assert runtime.teensy_status.relayOn is False
    assert runtime.teensy_status.loopTime == 450.0
    assert runtime.teensy_status.stabilityEnabled is True
    assert runtime.teensy_status.yawEnabled is True
    assert runtime.teensy_status.autoCorrectionEnabled is False
    assert runtime.teensy_status.sprayGunLevelingEnabled is True
    assert runtime.teensy_status.rollerSteeringEnabled is False
    assert runtime.teensy_status.swingDampingEnabled is True
    assert runtime.teensy_status.sprayGunLedOn is False
    assert runtime.shell_connectivity_status.winchAvailable is True
    assert runtime.shell_connectivity_status.wheelAvailable is True
    assert runtime.shell_connectivity_status.baseReachable is True
    assert runtime.shell_connectivity_status.endEffectorReachable is True
    assert runtime.shell_connectivity_status.endEffectorAvailable is True
    assert runtime.shell_connectivity_status.baseOnline is True
    assert runtime.shell_connectivity_status.baseStatus == 0x01
    assert runtime.shell_connectivity_status.endEffectorOnline is False
    assert runtime.shell_connectivity_status.endEffectorStatus == 0x02
    assert runtime.shell_connectivity_status.baseIpAddress == "10.0.0.2"
    assert runtime.shell_connectivity_status.endEffectorIpAddress == "10.0.0.3"
    assert json.loads(runtime.launcher_admin.getDeviceConfig("BASE")) == {
        "ip": "10.0.0.2",
        "port": "22",
        "username": "deck",
        "key_path": "~/.ssh/id_base",
    }
    assert runtime.launcher_admin.updateDeviceConfig("BASE", "10.0.0.20", "2200", "operator", "~/.ssh/id_new") is True
    runtime.launcher_admin.handleDeviceCommand("BASE", "Wheel", "start")
    assert runtime.bundle.ssh_controller.update_calls == [
        ("BASE", "10.0.0.20", "2200", "operator", "~/.ssh/id_new")
    ]
    assert runtime.bundle.ssh_controller.command_calls == [("BASE", "Wheel", "start")]
    assert "heartbeatHandler" not in runtime.engine.context.properties
    assert "sshHandler" not in runtime.engine.context.properties
    assert set(runtime.engine.context.properties) == set(module._EXPECTED_CONTEXT_PROPERTY_NAMES)
    assert [button for button, _ in runtime.steam_deck_handler.callbacks] == [
        "up", "down", "left", "right", "r4", "l4", "menu", "switch", "l5", "r5", "dot", "a", "l1"
    ]


def test_app_runtime_shutdown_cleans_resources_in_order(monkeypatch) -> None:
    module, runtime = _runtime_without_bootstrap(monkeypatch)
    call_log: list[str] = []

    runtime.status_timer = _StatusTimerRecorder()
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

    assert runtime.status_timer.stopped is True
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
    module = importlib.import_module("paint_controller.core.app_runtime")
    from tests.startup_smoke_support import _context_objects

    context_objects = _context_objects(monkeypatch, tmp_path)
    expected = set(module._EXPECTED_CONTEXT_PROPERTY_NAMES)
    actual = set(context_objects)

    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)

    assert not missing, f"Startup smoke fixture missing expected context properties: {missing}"
    assert not unexpected, f"Startup smoke fixture has unexpected context properties: {unexpected}"
