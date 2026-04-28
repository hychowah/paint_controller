"""Direct tests for the controller factory and bounded AppRuntime seams."""

from __future__ import annotations

import json
import importlib
from dataclasses import dataclass

from tests.fakes import FakeNode


class _CleanupRecorder:
    def __init__(self, name: str, call_log: list[str]) -> None:
        self.name = name
        self.call_log = call_log
        self.cleanup_calls = 0

    def cleanup(self) -> None:
        self.cleanup_calls += 1
        self.call_log.append(self.name)


class _LoggerRecorder:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.infos: list[str] = []

    def info(self, message: str) -> None:
        self.infos.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def _controller_factory_module():
    return importlib.import_module("paint_controller.core.controller_factory")


def _app_runtime_module():
    return importlib.import_module("paint_controller.core.app_runtime")


def test_controller_bundle_cleanup_runs_reverse_order_and_logs_errors() -> None:
    module = _controller_factory_module()
    call_log: list[str] = []
    logger = _LoggerRecorder()

    def cleanup_factory(name: str):
        return _CleanupRecorder(name, call_log)

    class BrokenCleanup:
        def cleanup(self) -> None:
            raise RuntimeError("boom")

    bundle = module.ControllerBundle(
        warning_handler=object(),
        system_monitor=cleanup_factory("system_monitor"),
        wheel_controller=cleanup_factory("wheel_controller"),
        esp32_valve_controller=cleanup_factory("esp32_valve_controller"),
        lidar_controller=cleanup_factory("lidar_controller"),
        wind_monitor=cleanup_factory("wind_monitor"),
        winch_controller=cleanup_factory("winch_controller"),
        teensy_controller=cleanup_factory("teensy_controller"),
        heartbeat_handler=cleanup_factory("heartbeat_handler"),
        safety_coordinator=object(),
        overlay_controller=cleanup_factory("overlay_controller"),
        control_processor=cleanup_factory("control_processor"),
        admin_action_gate=object(),
        manual_command_handler=object(),
        device_action_handler=object(),
        device_operations_handler=object(),
        winch_motion_handler=object(),
        tuning_admin_handler=object(),
        base_top_view_admin_handler=object(),
        input_handler=cleanup_factory("input_handler"),
        emergency_handler=BrokenCleanup(),
        ssh_controller=cleanup_factory("ssh_controller"),
        screen_manager=cleanup_factory("screen_manager"),
        screen_recorder=cleanup_factory("screen_recorder"),
        ros_bag_recorder=cleanup_factory("ros_bag_recorder"),
        workflow_catalog=cleanup_factory("workflow_catalog"),
        workflow_editor=cleanup_factory("workflow_editor"),
        workflow_runner=cleanup_factory("workflow_runner"),
    )

    bundle.cleanup(logger)

    assert call_log == [
        "workflow_editor",
        "workflow_runner",
        "workflow_catalog",
        "ros_bag_recorder",
        "screen_recorder",
        "screen_manager",
        "ssh_controller",
        "input_handler",
        "control_processor",
        "overlay_controller",
        "heartbeat_handler",
        "teensy_controller",
        "winch_controller",
        "wind_monitor",
        "lidar_controller",
        "esp32_valve_controller",
        "wheel_controller",
        "system_monitor",
    ]
    assert logger.errors == ["Error cleaning up emergency_handler: boom"]


def test_create_controllers_wires_dependency_graph(monkeypatch) -> None:
    module = _controller_factory_module()
    construction_log: list[tuple[str, tuple, dict]] = []

    def record(name: str):
        class Recorded:
            def __init__(self, *args, **kwargs) -> None:
                construction_log.append((name, args, kwargs))
                self.args = args
                self.kwargs = kwargs

        return Recorded

    hardware_calls: list[tuple[object, object, object]] = []

    class FakeHardwareControllers:
        @classmethod
        def from_controllers(cls, teensy, winch, esp32):
            hardware_calls.append((teensy, winch, esp32))
            return "hardware-bundle"

    monkeypatch.setattr(module, "WarningHandler", record("WarningHandler"))
    monkeypatch.setattr(module, "SystemMonitor", record("SystemMonitor"))
    monkeypatch.setattr(module, "WheelController", record("WheelController"))
    monkeypatch.setattr(module, "ESP32ValveController", record("ESP32ValveController"))
    monkeypatch.setattr(module, "LidarController", record("LidarController"))
    monkeypatch.setattr(module, "WindMonitor", record("WindMonitor"))
    monkeypatch.setattr(module, "WinchController", record("WinchController"))
    monkeypatch.setattr(module, "TeensyController", record("TeensyController"))
    monkeypatch.setattr(module, "SafetyCoordinator", record("SafetyCoordinator"))
    monkeypatch.setattr(module, "UIHeartbeatHandler", record("UIHeartbeatHandler"))
    monkeypatch.setattr(module, "JoystickSelectionModel", record("JoystickSelectionModel"))
    monkeypatch.setattr(module, "OverlayController", record("OverlayController"))
    monkeypatch.setattr(module, "ControlProcessor", record("ControlProcessor"))
    monkeypatch.setattr(module, "AdminActionGate", record("AdminActionGate"))
    monkeypatch.setattr(module, "ManualCommandHandler", record("ManualCommandHandler"))
    monkeypatch.setattr(module, "DeviceActionHandler", record("DeviceActionHandler"))
    monkeypatch.setattr(module, "DeviceOperationsHandler", record("DeviceOperationsHandler"))
    monkeypatch.setattr(module, "WinchMotionHandler", record("WinchMotionHandler"))
    monkeypatch.setattr(module, "TuningAdminHandler", record("TuningAdminHandler"))
    monkeypatch.setattr(module, "BaseTopViewAdminHandler", record("BaseTopViewAdminHandler"))
    monkeypatch.setattr(module, "WorkflowCatalog", record("WorkflowCatalog"))
    monkeypatch.setattr(module, "WorkflowEditor", record("WorkflowEditor"))
    monkeypatch.setattr(module, "WorkFlowRunner", record("WorkFlowRunner"))
    monkeypatch.setattr(module, "UIInputHandler", record("UIInputHandler"))
    monkeypatch.setattr(module, "EmergencyButtonHandler", record("EmergencyButtonHandler"))
    monkeypatch.setattr(module, "UISSHController", record("UISSHController"))
    monkeypatch.setattr(module, "ScreenManager", record("ScreenManager"))
    monkeypatch.setattr(module, "ScreenRecorder", record("ScreenRecorder"))
    monkeypatch.setattr(module, "RosBagRecorder", record("RosBagRecorder"))
    monkeypatch.setattr(module, "HardwareControllers", FakeHardwareControllers)

    node = FakeNode()
    settings_manager = object()
    state_store = object()
    steam_deck_handler = object()
    video_stream_handler = object()
    base_top_view_service = object()
    show_popup = object()
    close_popup = object()

    bundle = module.create_controllers(
        node=node,
        settings_manager=settings_manager,
        capability_catalog=object(),
        state_store=state_store,
        steam_deck_handler=steam_deck_handler,
        video_stream_handler=video_stream_handler,
        base_top_view_service=base_top_view_service,
        show_popup_fn=show_popup,
        close_popup_fn=close_popup,
    )

    assert hardware_calls == [(
        bundle.teensy_controller,
        bundle.winch_controller,
        bundle.esp32_valve_controller,
    )]
    assert bundle.workflow_catalog.kwargs["logger"] is node.get_logger()
    assert bundle.workflow_editor.kwargs["catalog"] is bundle.workflow_catalog
    assert bundle.workflow_editor.kwargs["logger"] is node.get_logger()
    assert bundle.overlay_controller.kwargs["selection_model"] is not None
    assert bundle.control_processor.kwargs["selection_model"] is bundle.overlay_controller.kwargs["selection_model"]
    assert bundle.workflow_runner.args == (node, "hardware-bundle")
    assert bundle.workflow_runner.kwargs["logger"] is node.get_logger()
    assert bundle.workflow_runner.kwargs["catalog"] is bundle.workflow_catalog
    assert bundle.admin_action_gate.kwargs["capability_catalog"] is not None
    assert bundle.admin_action_gate.kwargs["state_store"] is state_store
    assert bundle.manual_command_handler.kwargs["teensy"] is bundle.teensy_controller
    assert bundle.manual_command_handler.kwargs["winch"] is bundle.winch_controller
    assert bundle.manual_command_handler.kwargs["logger"] is node.get_logger()
    assert bundle.device_action_handler.kwargs["teensy"] is bundle.teensy_controller
    assert bundle.device_action_handler.kwargs["winch"] is bundle.winch_controller
    assert bundle.device_action_handler.kwargs["wheel"] is bundle.wheel_controller
    assert bundle.device_action_handler.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.device_action_handler.kwargs["logger"] is node.get_logger()
    assert bundle.device_operations_handler.kwargs["teensy"] is bundle.teensy_controller
    assert bundle.device_operations_handler.kwargs["winch"] is bundle.winch_controller
    assert bundle.device_operations_handler.kwargs["video_stream_handler"] is video_stream_handler
    assert bundle.device_operations_handler.kwargs["screen_recorder"] is bundle.screen_recorder
    assert bundle.device_operations_handler.kwargs["ros_bag_recorder"] is bundle.ros_bag_recorder
    assert bundle.device_operations_handler.kwargs["heartbeat_handler"] is bundle.heartbeat_handler
    assert bundle.device_operations_handler.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.device_operations_handler.kwargs["logger"] is node.get_logger()
    assert bundle.winch_motion_handler.kwargs["winch"] is bundle.winch_controller
    assert bundle.winch_motion_handler.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.winch_motion_handler.kwargs["logger"] is node.get_logger()
    assert bundle.tuning_admin_handler.kwargs["teensy"] is bundle.teensy_controller
    assert bundle.tuning_admin_handler.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.tuning_admin_handler.kwargs["logger"] is node.get_logger()
    assert bundle.base_top_view_admin_handler.kwargs["base_top_view_service"] is base_top_view_service
    assert bundle.base_top_view_admin_handler.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.base_top_view_admin_handler.kwargs["logger"] is node.get_logger()
    assert bundle.input_handler.kwargs["selection_model"] is bundle.overlay_controller.kwargs["selection_model"]
    assert bundle.input_handler.kwargs["close_popup_fn"] is close_popup
    assert bundle.emergency_handler.kwargs["safety_coordinator"] is bundle.safety_coordinator
    assert bundle.screen_recorder.kwargs["screen_manager"] is bundle.screen_manager
    assert node.get_logger().records[-1].message == "All controllers created with explicit DI"


@dataclass
class _ContextRecorder:
    properties: dict[str, object]

    def setContextProperty(self, name: str, obj: object) -> None:
        self.properties[name] = obj


class _EngineRecorder:
    def __init__(self) -> None:
        self.context = _ContextRecorder({})

    def rootContext(self) -> _ContextRecorder:
        return self.context


class _SignalRecorder:
    def __init__(self) -> None:
        self.connections: list[tuple[object, tuple]] = []

    def connect(self, callback, *args) -> None:
        self.connections.append((callback, args))


class _SteamDeckHandlerRecorder:
    def __init__(self) -> None:
        self.callbacks: list[tuple[str, object]] = []

    def register_button_callback(self, button_name: str, callback) -> None:
        self.callbacks.append((button_name, callback))


class _InputHandlerRecorder:
    def on_up_pressed(self) -> None: pass
    def on_down_pressed(self) -> None: pass
    def on_left_pressed(self) -> None: pass
    def on_right_pressed(self) -> None: pass
    def on_r4_pressed(self) -> None: pass
    def on_l4_pressed(self) -> None: pass
    def on_menu_pressed(self) -> None: pass
    def on_switch_pressed(self) -> None: pass
    def on_l5_pressed(self) -> None: pass
    def on_r5_pressed(self) -> None: pass
    def on_l1_pressed(self) -> None: pass


class _QtBridgeRecorder:
    def __init__(self) -> None:
        self.status_updated = _SignalRecorder()
        self.emergency_overlay_changed = type("Emitter", (), {"emit": lambda self, *args: None})()
        self.emergency_triggered = type("Emitter", (), {"emit": lambda self, *args: None})()
        self.frame_ready = type("Emitter", (), {"emit": lambda self, *args: None})()
        self.show_popup_calls: list[tuple[str, str, str, int]] = []
        self.base_top_view_service = None
        self.input_handler = None

    def show_popup(self, title: str, message: str, popup_type: str, delay: int) -> None:
        self.show_popup_calls.append((title, message, popup_type, delay))

    def close_popup(self) -> None:
        pass

    def toggle_fullscreen(self) -> None:
        pass

    def toggle_lidar_overlay(self) -> None:
        pass

    def set_base_top_view_service(self, service) -> None:
        self.base_top_view_service = service

    def set_input_handler(self, input_handler) -> None:
        self.input_handler = input_handler


class _WheelControllerRecorder:
    def __init__(self) -> None:
        self.available_changed = _SignalRecorder()
        self.enabled_changed = _SignalRecorder()
        self.left_motor_available_changed = _SignalRecorder()
        self.right_motor_available_changed = _SignalRecorder()
        self.left_wheel_speed_changed = _SignalRecorder()
        self.right_wheel_speed_changed = _SignalRecorder()
        self.left_wheel_current_changed = _SignalRecorder()
        self.right_wheel_current_changed = _SignalRecorder()
        self.left_wheel_position_changed = _SignalRecorder()
        self.right_wheel_position_changed = _SignalRecorder()
        self.error_state_changed = _SignalRecorder()
        self.available = True
        self.enabled = True
        self.left_motor_available = True
        self.right_motor_available = False
        self.left_wheel_speed = 1.5
        self.right_wheel_speed = -2.5
        self.left_wheel_current = 3.0
        self.right_wheel_current = 4.0
        self.left_wheel_position = 125.0
        self.right_wheel_position = 225.0


class _EmergencyHandlerRecorder:
    def __init__(self) -> None:
        self.overlay_changed = _SignalRecorder()
        self.emergency_triggered = _SignalRecorder()

    def check_emergency_button(self, _buttons) -> None:
        pass


class _ControlProcessorRecorder:
    def __init__(self) -> None:
        self.left_control_mode = "None"
        self.left_control_value = ""
        self.right_control_mode = "None"
        self.right_control_value = ""
        self.left_control_mode_changed = _SignalRecorder()
        self.left_control_value_changed = _SignalRecorder()
        self.right_control_mode_changed = _SignalRecorder()
        self.right_control_value_changed = _SignalRecorder()

    def process_input(self, _input_state) -> None:
        pass


class _VideoHandlerRecorder:
    def __init__(self) -> None:
        self.endEffectorFrameReady = _SignalRecorder()
        self.baseFrontFrameReady = _SignalRecorder()
        self.baseRearFrameReady = _SignalRecorder()
        self.recordingStatusChanged = _SignalRecorder()
        self.baseRecordingStatusChanged = _SignalRecorder()
        self.is_recording = True
        self.is_base_recording = False
        self.started = 0

    def start_all_streams(self) -> int:
        self.started += 1
        return 4


class _SshControllerRecorder:
    def __init__(self) -> None:
        self.deviceAvailabilityChanged = _SignalRecorder()
        self.configUpdated = _SignalRecorder()
        self.deviceAvailability = {"BASE": True, "END_EFFECTOR": True}
        self.devicePingTimes = {"BASE": "42", "END_EFFECTOR": "38"}
        self.update_calls: list[tuple[str, str, str, str, str]] = []
        self.command_calls: list[tuple[str, str, str]] = []

    def get_device_config(self, device_name: str) -> str:
        configs = {
            "BASE": {"ip": "10.0.0.2", "port": "22", "username": "deck", "key_path": "~/.ssh/id_base"},
            "END_EFFECTOR": {"ip": "10.0.0.3", "port": "22", "username": "deck", "key_path": "~/.ssh/id_ef"},
        }
        return json.dumps(configs.get(device_name, {}))

    def update_device_config(self, device_name: str, ip: str, port: str, username: str, key_path: str) -> bool:
        self.update_calls.append((device_name, ip, port, username, key_path))
        return True

    def handle_device_command(self, device_name: str, service_name: str, action: str) -> None:
        self.command_calls.append((device_name, service_name, action))


class _ScreenRecorderRecorder:
    def __init__(self) -> None:
        self.is_recording_changed = _SignalRecorder()
        self.recording_duration_changed = _SignalRecorder()
        self.free_space_gb_changed = _SignalRecorder()
        self.is_recording = False
        self.recording_duration = 120
        self.free_space_gb = 8.5


class _RosBagRecorderRecorder:
    def __init__(self) -> None:
        self.is_bag_recording_changed = _SignalRecorder()
        self.bag_recording_duration_changed = _SignalRecorder()
        self.is_compressing_changed = _SignalRecorder()
        self.bag_status_message_changed = _SignalRecorder()
        self.is_bag_recording = True
        self.bag_recording_duration = 33
        self.is_compressing = False
        self.bag_status_message = "Remote EF ready"


class _SystemMonitorRecorder:
    def __init__(self) -> None:
        self.battery_level_changed = _SignalRecorder()
        self.battery_remaining_time_changed = _SignalRecorder()
        self.cpu_temperature_changed = _SignalRecorder()
        self.battery_level = 100
        self.battery_remaining_time = "N/A"
        self.cpu_temperature = 0.0


class _TeensyControllerRecorder:
    def __init__(self) -> None:
        self.status_changed = _SignalRecorder()
        self.connection_changed = _SignalRecorder()
        self.available = True
        self.stability_enabled = True
        self.auto_correction_enabled = False
        self.spray_gun_leveling_enabled = True
        self.roller_steering_enabled = False
        self.swing_damping_enabled = True
        self.spray_gun_led_on = False
        self.all_status = {
            "enabled": True,
            "relay_on": False,
            "voltage": 24.0,
            "current": 1.2,
            "temperature": 32.0,
            "run_time": 120.0,
            "loop_time": 450.0,
            "loop_time_counter": 900.0,
            "imu_pitch": 1.5,
            "imu_roll": -0.5,
            "imu_yaw": 3.0,
            "imu_acc_x": 0.1,
            "imu_acc_y": 0.2,
            "imu_acc_z": 0.3,
            "imu_angular_acc_x": 0.4,
            "imu_angular_acc_y": 0.5,
            "imu_angular_acc_z": 0.6,
            "arm_extension_dist": 320.0,
            "arm_rail_current": 40.0,
            "gimbal_pitch_motor_current": 20.0,
            "gimbal_pitch_motor_angle": -4.5,
            "yaw_enabled": True,
        }


class _ValveStatusRecorder:
    def __init__(self) -> None:
        self.valve_position_changed = _SignalRecorder()
        self.valve_rate_changed = _SignalRecorder()
        self.total_volume_changed = _SignalRecorder()
        self.valve_motor_current_changed = _SignalRecorder()
        self.valve_motor_connected_changed = _SignalRecorder()
        self.flow_meter_connected_changed = _SignalRecorder()
        self.esp32_connected_changed = _SignalRecorder()
        self.valve_position = 42.0
        self.valve_rate = 1.5
        self.total_volume = 8.0
        self.valve_motor_current = 0.7
        self.valve_motor_connected = True
        self.flow_meter_connected = False
        self.esp32_connected = True


class _LidarStatusRecorder:
    def __init__(self) -> None:
        self.distance_changed = _SignalRecorder()
        self.angle_changed = _SignalRecorder()
        self.distance = 1.25
        self.angle = -3.5


class _WinchStatusRecorder:
    def __init__(self) -> None:
        self.available_changed = _SignalRecorder()
        self.enabled_changed = _SignalRecorder()
        self.load_detection_changed = _SignalRecorder()
        self.cable_length_changed = _SignalRecorder()
        self.cable_speed_changed = _SignalRecorder()
        self.winch_torque_changed = _SignalRecorder()
        self.motor_temperature_changed = _SignalRecorder()
        self.motor_voltage_changed = _SignalRecorder()
        self.motor_brake_changed = _SignalRecorder()
        self.unusual_load_detected_changed = _SignalRecorder()
        self.available = True
        self.enabled = False
        self.load_detection_enabled = True
        self.cable_length = 1200.0
        self.cable_speed = 15.0
        self.winch_torque = 12.5
        self.motor_temperature = 31.0
        self.motor_voltage = 24.0
        self.motor_brake = True
        self.unusual_load_detected = False


class _HeartbeatHandlerRecorder:
    def __init__(self) -> None:
        self.base_online_changed = _SignalRecorder()
        self.base_status_changed = _SignalRecorder()
        self.ef_online_changed = _SignalRecorder()
        self.ef_status_changed = _SignalRecorder()
        self.base_online = True
        self.base_status = 0x01
        self.ef_online = False
        self.ef_status = 0x02


class _SafetyCoordinatorRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def halt_all_effectors(self, reason: str, heartbeat_state=None) -> None:
        self.calls.append((reason, heartbeat_state))


class _StatusTimerRecorder:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class _WaitableRecorder:
    def __init__(self, name: str, call_log: list[str]) -> None:
        self.name = name
        self.call_log = call_log
        self.shutdown_requested = False
        self.wait_calls: list[int] = []
        self.terminated = False

    def request_shutdown(self) -> None:
        self.shutdown_requested = True
        self.call_log.append(f"{self.name}.request_shutdown")

    def wait(self, timeout: int) -> bool:
        self.wait_calls.append(timeout)
        self.call_log.append(f"{self.name}.wait({timeout})")
        return True

    def terminate(self) -> None:
        self.terminated = True
        self.call_log.append(f"{self.name}.terminate")


def _runtime_without_bootstrap(monkeypatch):
    module = _app_runtime_module()
    monkeypatch.setattr(module.AppRuntime, "_bootstrap", lambda self: None)
    return module, module.AppRuntime(argv=[])


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
            "winch_motion_handler": object(),
            "tuning_admin_handler": object(),
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
    assert runtime.system_control_services.manualCommandHandler is runtime.bundle.manual_command_handler
    assert runtime.video_runtime.controls.leftMode == "None"
    assert runtime.video_runtime.topBar.systemBatteryPercent == 100
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


def test_admin_action_gate_evaluates_idle_default_and_live_exceptions() -> None:
    gate_module = importlib.import_module("paint_controller.models.admin_action_gate")

    class FakeCapabilityCatalog:
        def getActionCapability(self, key: str):
            mapping = {
                "tuning.short_yaw_pid": {
                    "title": "Short Yaw PID",
                    "legalStateClass": "tuning-calibration",
                },
                "status.winch_enable": {
                    "title": "Winch Enable Toggle",
                    "legalStateClass": "status-admin",
                },
            }
            return mapping.get(key, {})

    state_store = type("StateStore", (), {"controller_heartbeat_state": 1})()
    gate = gate_module.AdminActionGate(
        capability_catalog=FakeCapabilityCatalog(),
        state_store=state_store,
    )

    tuning_eval = gate.evaluate("tuning.short_yaw_pid")
    status_eval = gate.evaluate("status.winch_enable")

    assert tuning_eval["allowed"] is False
    assert tuning_eval["reason"] == "Short Yaw PID requires the system to be idle"
    assert status_eval["allowed"] is True


def test_admin_action_gate_allows_emergency_override_in_error_state() -> None:
    gate_module = importlib.import_module("paint_controller.models.admin_action_gate")
    state_store = type("StateStore", (), {"controller_heartbeat_state": 3})()
    gate = gate_module.AdminActionGate(capability_catalog=None, state_store=state_store)

    evaluation = gate.evaluate("winch.emergency_stop")

    assert evaluation["allowed"] is True


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
    module = _app_runtime_module()
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