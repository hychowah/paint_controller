"""Shared helpers for controller-factory and AppRuntime tests."""

from __future__ import annotations

import importlib
import json
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
        self.emits: list[tuple[object, ...]] = []

    def connect(self, callback, *args) -> None:
        self.connections.append((callback, args))

    def emit(self, *args) -> None:
        self.emits.append(args)


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
        self.emergency_overlay_changed = _SignalRecorder()
        self.emergency_triggered = _SignalRecorder()
        self.frame_ready = _SignalRecorder()
        self.toggleVideoOverlayRequested = _SignalRecorder()
        self.updateVideoSourceRequested = _SignalRecorder()
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

    def update_fullscreen_video_source(self) -> None:
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
        self.monitoring_started = False

    def start_monitoring(self, interval_ms: int = 1000) -> None:
        self.monitoring_started = True


class _TeensyControllerRecorder:
    def __init__(self) -> None:
        self.status_changed = _SignalRecorder()
        self.connection_changed = _SignalRecorder()
        self.stability_enabled_changed = _SignalRecorder()
        self.auto_correction_enabled_changed = _SignalRecorder()
        self.spray_gun_leveling_changed = _SignalRecorder()
        self.roller_steering_enabled_changed = _SignalRecorder()
        self.swing_damping_enabled_changed = _SignalRecorder()
        self.spray_gun_led_changed = _SignalRecorder()
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
            "yaw_command": 5.0,
            "yaw_pid_p": 0.1,
            "yaw_pid_i": 0.2,
            "yaw_pid_d": 0.3,
            "imu_acc_x": 0.1,
            "imu_acc_y": 0.2,
            "imu_acc_z": 0.3,
            "imu_angular_acc_x": 0.4,
            "imu_angular_acc_y": 0.5,
            "imu_angular_acc_z": 0.6,
            "arm_extension_dist": 320.0,
            "arm_rail_current": 40.0,
            "gimbal_pitch_motor_angle": -4.5,
            "top_rail_position": 100.0,
            "top_rail_speed": 5.0,
            "top_rail_current": 2.0,
            "arm_rail_position": 200.0,
            "arm_rail_speed": 3.0,
            "arm_sensor_dist": 150.0,
            "left_prop_position": 10.0,
            "right_prop_position": 20.0,
            "left_prop_pwm": 1200,
            "right_prop_pwm": 1300,
            "spray_gun_pitch": 45.0,
            "gimbal_pitch_motor_current": 20.0,
            "gimbal_pitch_motor_temp": 35.0,
            "gimbal_roll_motor_angle": 5.0,
            "gimbal_roll_motor_current": 15.0,
            "gimbal_roll_motor_temp": 36.0,
            "spray_gun_trigger": True,
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


class _BaseTopViewServiceRecorder:
    def __init__(self) -> None:
        self.zoomChanged = _SignalRecorder()
        self.offsetXChanged = _SignalRecorder()
        self.offsetYChanged = _SignalRecorder()
        self.cropEnabledChanged = _SignalRecorder()
        self.cropWidthRatioChanged = _SignalRecorder()
        self.cropCenterXChanged = _SignalRecorder()
        self.k1Changed = _SignalRecorder()
        self.k2Changed = _SignalRecorder()
        self.k3Changed = _SignalRecorder()
        self.k4Changed = _SignalRecorder()
        self.editModeChanged = _SignalRecorder()
        self.enabledChanged = _SignalRecorder()
        self.sourcePointsChanged = _SignalRecorder()
        self.frameReady = _SignalRecorder()
        self.enabled = True
        self.editMode = False
        self.zoom = 0.51
        self.offsetX = 0.026
        self.offsetY = 0.474
        self.cropEnabled = True
        self.cropWidthRatio = 0.9
        self.cropCenterX = 0.5
        self.k1 = -0.389
        self.k2 = 0.142
        self.k3 = 0.0
        self.k4 = 0.0
        self.sourcePoints = [[0.012, 1.0], [0.988, 1.0], [0.837, 0.727], [0.372, 0.727]]


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
        self.started = False
        self.timeout = _SignalRecorder()

    def stop(self) -> None:
        self.stopped = True

    def start(self, _interval_ms: int) -> None:
        self.started = True


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