"""Compose the QML root-context property dict and status wrappers."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Property, QObject, Signal, Slot

if TYPE_CHECKING:
    from paint_controller.core.app_runtime import AppRuntime

logger = logging.getLogger(__name__)

_EXPECTED_CONTEXT_PROPERTY_NAMES: tuple[str, ...] = (
    "stateStore",
    "backend",
    "shellState",
    "overlayHost",
    "actionLegality",
    "systemControlServices",
    "videoRuntime",
    "recordingStatus",
    "wheelStatus",
    "winchStatus",
    "teensyStatus",
    "valveStatus",
    "lidarStatus",
    "shellConnectivityStatus",
    "launcherAdmin",
    "overlayController",
    "warningHandler",
    "wheelActions",
    "winchActions",
    "tuningActions",
    "recordingActions",
    "teensyActions",
    "systemActions",
    "baseTopViewActions",
    "baseTopViewStatus",
    "shellRouter",
    "deviceActionHandler",
    "settingsManager",
)


def _connect_if_signal(owner: object, signal_name: str, callback: Callable[..., None]) -> None:
    signal = getattr(owner, signal_name, None)
    if signal is None or not hasattr(signal, "connect"):
        return
    signal.connect(lambda *_args, **_kwargs: callback())


def _read_mapping_value(mapping: Any, key: str) -> Any:
    if isinstance(mapping, dict):
        return mapping.get(key)
    property_fn = getattr(mapping, "property", None)
    if callable(property_fn):
        value = property_fn(key)
        if value is not None:
            return value
    return getattr(mapping, key, None)


def _read_object_value(owner: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(owner, name):
            return getattr(owner, name)
        property_fn = getattr(owner, "property", None)
        if callable(property_fn):
            value = property_fn(name)
            if value is not None:
                return value
    return default


class _SystemControlServices(QObject):
    def __init__(self, workflow_runner: object, workflow_editor: object, manual_command_handler: object) -> None:
        super().__init__()
        self._workflow_runner = workflow_runner
        self._workflow_editor = workflow_editor
        self._manual_command_handler = manual_command_handler

    @Property(QObject, constant=True)
    def workflowRunner(self) -> QObject:
        return self._workflow_runner

    @Property(QObject, constant=True)
    def workflowEditor(self) -> QObject:
        return self._workflow_editor

    @Property(QObject, constant=True)
    def manualCommandHandler(self) -> QObject:
        return self._manual_command_handler


class _VideoRuntimeControls(QObject):
    changed = Signal()

    def __init__(self, control_processor: object) -> None:
        super().__init__()
        self._control_processor = control_processor
        for signal_name in (
            "left_control_mode_changed",
            "left_control_value_changed",
            "right_control_mode_changed",
            "right_control_value_changed",
            "left_control_mode_display_changed",
            "right_control_mode_display_changed",
        ):
            _connect_if_signal(control_processor, signal_name, self.changed.emit)

    @Property(str, notify=changed)
    def leftMode(self) -> str:
        return str(_read_object_value(self._control_processor, "left_control_mode", default=""))

    @Property(str, notify=changed)
    def leftValue(self) -> str:
        return str(_read_object_value(self._control_processor, "left_control_value", default=""))

    @Property(str, notify=changed)
    def rightMode(self) -> str:
        return str(_read_object_value(self._control_processor, "right_control_mode", default=""))

    @Property(str, notify=changed)
    def rightValue(self) -> str:
        return str(_read_object_value(self._control_processor, "right_control_value", default=""))

    @Property(str, notify=changed)
    def leftModeDisplay(self) -> str:
        return str(
            _read_object_value(self._control_processor, "left_control_mode_display", default="")
        )

    @Property(str, notify=changed)
    def rightModeDisplay(self) -> str:
        return str(
            _read_object_value(self._control_processor, "right_control_mode_display", default="")
        )


class _VideoRuntimeFeeds(QObject):
    endEffectorFrameReady = Signal()
    baseFrontFrameReady = Signal()
    baseRearFrameReady = Signal()

    def __init__(self, video_stream_handler: object) -> None:
        super().__init__()
        _connect_if_signal(video_stream_handler, "endEffectorFrameReady", self.endEffectorFrameReady.emit)
        _connect_if_signal(video_stream_handler, "baseFrontFrameReady", self.baseFrontFrameReady.emit)
        _connect_if_signal(video_stream_handler, "baseRearFrameReady", self.baseRearFrameReady.emit)


class _VideoRuntimeTopBar(QObject):
    changed = Signal()
    endEffectorVideoRequested = Signal()
    baseVideoRequested = Signal()

    def __init__(
        self,
        ssh_controller: object,
        screen_recorder: object,
        system_monitor: object,
        teensy_controller: object,
        winch_controller: object,
    ) -> None:
        super().__init__()
        self._ssh_controller = ssh_controller
        self._screen_recorder = screen_recorder
        self._system_monitor = system_monitor
        self._teensy_controller = teensy_controller
        self._winch_controller = winch_controller

        for owner, signal_names in (
            (ssh_controller, ("deviceAvailabilityChanged",)),
            (screen_recorder, ("is_recording_changed", "recording_duration_changed")),
            (system_monitor, (
                "battery_level_changed",
                "battery_remaining_time_changed",
                "cpu_temperature_changed",
            )),
            (teensy_controller, ("status_changed",)),
            (winch_controller, ("motor_voltage_changed",)),
        ):
            for signal_name in signal_names:
                _connect_if_signal(owner, signal_name, self.changed.emit)

    def _ping_ms(self, device_name: str) -> float:
        ping_times = _read_object_value(self._ssh_controller, "devicePingTimes", default={})
        value = _read_mapping_value(ping_times, device_name)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _teensy_voltage(self) -> float:
        all_status = _read_object_value(self._teensy_controller, "all_status", default={})
        value = _read_mapping_value(all_status, "voltage")
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def endEffectorPingMs(self) -> float:
        return self._ping_ms("END_EFFECTOR")

    @Property(float, notify=changed)
    def basePingMs(self) -> float:
        return self._ping_ms("BASE")

    def _device_available(self, device_name: str) -> bool:
        device_availability = _read_object_value(self._ssh_controller, "deviceAvailability", default={})
        if isinstance(device_availability, dict):
            return bool(device_availability.get(device_name, False))
        return False

    @Property(bool, notify=changed)
    def endEffectorConnected(self) -> bool:
        return self._device_available("END_EFFECTOR")

    @Property(bool, notify=changed)
    def baseConnected(self) -> bool:
        return self._device_available("BASE")

    @Property(float, notify=changed)
    def endEffectorBatteryVoltage(self) -> float:
        return self._teensy_voltage()

    @Property(float, notify=changed)
    def baseBatteryVoltage(self) -> float:
        value = _read_object_value(self._winch_controller, "motor_voltage", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(bool, notify=changed)
    def isRecording(self) -> bool:
        return bool(_read_object_value(self._screen_recorder, "is_recording", "isRecording", default=False))

    @Property(int, notify=changed)
    def recordingDuration(self) -> int:
        value = _read_object_value(self._screen_recorder, "recording_duration", default=0)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @Property(int, notify=changed)
    def systemBatteryPercent(self) -> int:
        value = _read_object_value(
            self._system_monitor,
            "battery_level",
            "battery_percentage",
            default=0,
        )
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @Property(float, notify=changed)
    def cpuTemperature(self) -> float:
        value = _read_object_value(self._system_monitor, "cpu_temperature", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(str, notify=changed)
    def batteryRemainingTime(self) -> str:
        value = _read_object_value(
            self._system_monitor,
            "battery_remaining_time",
            "battery_time_remaining",
            default="N/A",
        )
        return str(value if value is not None else "N/A")

    @Slot()
    def requestEndEffectorVideo(self) -> None:
        self.endEffectorVideoRequested.emit()

    @Slot()
    def requestBaseVideo(self) -> None:
        self.baseVideoRequested.emit()


class _VideoRuntime(QObject):
    def __init__(
        self,
        control_processor: object,
        video_stream_handler: object,
        ssh_controller: object,
        screen_recorder: object,
        system_monitor: object,
        teensy_controller: object,
        winch_controller: object,
    ) -> None:
        super().__init__()
        self._controls = _VideoRuntimeControls(control_processor)
        self._feeds = _VideoRuntimeFeeds(video_stream_handler)
        self._top_bar = _VideoRuntimeTopBar(
            ssh_controller=ssh_controller,
            screen_recorder=screen_recorder,
            system_monitor=system_monitor,
            teensy_controller=teensy_controller,
            winch_controller=winch_controller,
        )

    @Property(QObject, constant=True)
    def controls(self) -> QObject:
        return self._controls

    @Property(QObject, constant=True)
    def feeds(self) -> QObject:
        return self._feeds

    @Property(QObject, constant=True)
    def topBar(self) -> QObject:
        return self._top_bar


class _RecordingStatus(QObject):
    changed = Signal()

    def __init__(self, video_stream_handler: object, screen_recorder: object, ros_bag_recorder: object) -> None:
        super().__init__()
        self._video_stream_handler = video_stream_handler
        self._screen_recorder = screen_recorder
        self._ros_bag_recorder = ros_bag_recorder

        for owner, signal_names in (
            (video_stream_handler, ("recordingStatusChanged", "baseRecordingStatusChanged")),
            (screen_recorder, ("is_recording_changed", "recording_duration_changed", "free_space_gb_changed")),
            (ros_bag_recorder, (
                "is_bag_recording_changed",
                "bag_recording_duration_changed",
                "is_compressing_changed",
                "bag_status_message_changed",
            )),
        ):
            for signal_name in signal_names:
                _connect_if_signal(owner, signal_name, self.changed.emit)

    @Property(bool, notify=changed)
    def endEffectorRecording(self) -> bool:
        return bool(_read_object_value(self._video_stream_handler, "is_recording", default=False))

    @Property(bool, notify=changed)
    def baseRecording(self) -> bool:
        return bool(_read_object_value(self._video_stream_handler, "is_base_recording", default=False))

    @Property(bool, notify=changed)
    def screenRecording(self) -> bool:
        return bool(_read_object_value(self._screen_recorder, "is_recording", "isRecording", default=False))

    @Property(int, notify=changed)
    def screenRecordingDuration(self) -> int:
        value = _read_object_value(self._screen_recorder, "recording_duration", default=0)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @Property(float, notify=changed)
    def screenFreeSpaceGb(self) -> float:
        value = _read_object_value(self._screen_recorder, "free_space_gb", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(bool, notify=changed)
    def rosBagRecording(self) -> bool:
        return bool(_read_object_value(self._ros_bag_recorder, "is_bag_recording", default=False))

    @Property(int, notify=changed)
    def rosBagRecordingDuration(self) -> int:
        value = _read_object_value(self._ros_bag_recorder, "bag_recording_duration", default=0)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @Property(bool, notify=changed)
    def rosBagCompressing(self) -> bool:
        return bool(_read_object_value(self._ros_bag_recorder, "is_compressing", default=False))

    @Property(str, notify=changed)
    def rosBagStatusMessage(self) -> str:
        value = _read_object_value(self._ros_bag_recorder, "bag_status_message", default="")
        return str(value if value is not None else "")


class _ShellConnectivityStatus(QObject):
    changed = Signal()

    def __init__(
        self,
        ssh_controller: object,
        heartbeat_handler: object,
        winch_controller: object,
        wheel_status: object,
        teensy_controller: object,
    ) -> None:
        super().__init__()
        self._ssh_controller = ssh_controller
        self._heartbeat_handler = heartbeat_handler
        self._winch_controller = winch_controller
        self._wheel_status = wheel_status
        self._teensy_controller = teensy_controller

        for owner, signal_names in (
            (ssh_controller, ("deviceAvailabilityChanged", "configUpdated")),
            (heartbeat_handler, (
                "base_online_changed",
                "base_status_changed",
                "ef_online_changed",
                "ef_status_changed",
            )),
            (winch_controller, ("available_changed",)),
            (wheel_status, ("changed",)),
            (teensy_controller, ("connection_changed",)),
        ):
            for signal_name in signal_names:
                _connect_if_signal(owner, signal_name, self.changed.emit)

    def _device_ip_address(self, device_name: str) -> str:
        get_device_config = getattr(self._ssh_controller, "get_device_config", None)
        if not callable(get_device_config):
            return "--"

        try:
            payload = get_device_config(device_name)
        except Exception:
            return "--"

        if isinstance(payload, str):
            try:
                config = json.loads(payload)
            except (TypeError, ValueError, json.JSONDecodeError):
                return "--"
        elif isinstance(payload, dict):
            config = payload
        else:
            return "--"

        ip_address = config.get("ip")
        return str(ip_address).strip() or "--"

    def _device_available(self, device_name: str) -> bool:
        device_availability = _read_object_value(self._ssh_controller, "deviceAvailability", default={})
        if isinstance(device_availability, dict):
            return bool(device_availability.get(device_name, False))
        return False

    @Property(bool, notify=changed)
    def baseReachable(self) -> bool:
        return self._device_available("BASE")

    @Property(bool, notify=changed)
    def endEffectorReachable(self) -> bool:
        return self._device_available("END_EFFECTOR")

    @Property(bool, notify=changed)
    def winchAvailable(self) -> bool:
        return bool(_read_object_value(self._winch_controller, "available", default=False))

    @Property(bool, notify=changed)
    def wheelAvailable(self) -> bool:
        return bool(_read_object_value(self._wheel_status, "available", default=False))

    @Property(bool, notify=changed)
    def endEffectorAvailable(self) -> bool:
        return bool(_read_object_value(self._teensy_controller, "available", default=False))

    @Property(bool, notify=changed)
    def baseOnline(self) -> bool:
        return bool(_read_object_value(self._heartbeat_handler, "base_online", default=False))

    @Property(int, notify=changed)
    def baseStatus(self) -> int:
        value = _read_object_value(self._heartbeat_handler, "base_status", default=0)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @Property(bool, notify=changed)
    def endEffectorOnline(self) -> bool:
        return bool(_read_object_value(self._heartbeat_handler, "ef_online", default=False))

    @Property(int, notify=changed)
    def endEffectorStatus(self) -> int:
        value = _read_object_value(self._heartbeat_handler, "ef_status", default=0)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @Property(str, notify=changed)
    def baseIpAddress(self) -> str:
        return self._device_ip_address("BASE")

    @Property(str, notify=changed)
    def endEffectorIpAddress(self) -> str:
        return self._device_ip_address("END_EFFECTOR")


class _LauncherAdmin(QObject):
    def __init__(self, ssh_controller: object) -> None:
        super().__init__()
        self._ssh_controller = ssh_controller

    @Slot(str, result=str)
    def getDeviceConfig(self, device_name: str) -> str:
        get_device_config = getattr(self._ssh_controller, "get_device_config", None)
        if not callable(get_device_config):
            return "{}"

        try:
            payload = get_device_config(device_name)
        except Exception:
            return "{}"

        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            try:
                return json.dumps(payload)
            except (TypeError, ValueError):
                return "{}"
        return "{}"

    @Slot(str, str, str, str, str, result=bool)
    def updateDeviceConfig(self, device_name: str, ip: str, port: str, username: str, key_path: str) -> bool:
        update_device_config = getattr(self._ssh_controller, "update_device_config", None)
        if not callable(update_device_config):
            return False

        try:
            return bool(update_device_config(device_name, ip, port, username, key_path))
        except Exception:
            return False

    @Slot(str, str, str)
    def handleDeviceCommand(self, device_name: str, service_name: str, action: str) -> None:
        handle_device_command = getattr(self._ssh_controller, "handle_device_command", None)
        if not callable(handle_device_command):
            return

        try:
            handle_device_command(device_name, service_name, action)
        except Exception:
            return


class _WinchStatus(QObject):
    changed = Signal()

    def __init__(self, winch_controller: object) -> None:
        super().__init__()
        self._winch_controller = winch_controller
        for signal_name in (
            "available_changed",
            "enabled_changed",
            "load_detection_changed",
            "cable_length_changed",
            "cable_speed_changed",
            "winch_torque_changed",
            "motor_temperature_changed",
            "motor_voltage_changed",
            "motor_brake_changed",
            "unusual_load_detected_changed",
        ):
            _connect_if_signal(winch_controller, signal_name, self.changed.emit)

    @Property(bool, notify=changed)
    def available(self) -> bool:
        return bool(_read_object_value(self._winch_controller, "available", default=False))

    @Property(bool, notify=changed)
    def enabled(self) -> bool:
        return bool(_read_object_value(self._winch_controller, "enabled", default=False))

    @Property(bool, notify=changed)
    def loadDetectionEnabled(self) -> bool:
        return bool(_read_object_value(self._winch_controller, "load_detection_enabled", default=False))

    @Property(float, notify=changed)
    def cableLength(self) -> float:
        value = _read_object_value(self._winch_controller, "cable_length", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def cableSpeed(self) -> float:
        value = _read_object_value(self._winch_controller, "cable_speed", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def winchTorque(self) -> float:
        value = _read_object_value(self._winch_controller, "winch_torque", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def motorTemperature(self) -> float:
        value = _read_object_value(self._winch_controller, "motor_temperature", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def motorVoltage(self) -> float:
        value = _read_object_value(self._winch_controller, "motor_voltage", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(bool, notify=changed)
    def motorBrake(self) -> bool:
        return bool(_read_object_value(self._winch_controller, "motor_brake", default=False))

    @Property(bool, notify=changed)
    def unusualLoadDetected(self) -> bool:
        return bool(_read_object_value(self._winch_controller, "unusual_load_detected", default=False))


class _WheelStatus(QObject):
    changed = Signal()

    def __init__(self, wheel_controller: object) -> None:
        super().__init__()
        self._wheel_controller = wheel_controller
        for signal_name in (
            "available_changed",
            "enabled_changed",
            "left_motor_available_changed",
            "right_motor_available_changed",
            "left_wheel_speed_changed",
            "right_wheel_speed_changed",
            "left_wheel_current_changed",
            "right_wheel_current_changed",
            "left_wheel_position_changed",
            "right_wheel_position_changed",
        ):
            _connect_if_signal(wheel_controller, signal_name, self.changed.emit)

    @Property(bool, notify=changed)
    def available(self) -> bool:
        return bool(_read_object_value(self._wheel_controller, "available", default=False))

    @Property(bool, notify=changed)
    def enabled(self) -> bool:
        return bool(_read_object_value(self._wheel_controller, "enabled", default=False))

    @Property(bool, notify=changed)
    def leftMotorAvailable(self) -> bool:
        return bool(_read_object_value(self._wheel_controller, "left_motor_available", default=False))

    @Property(bool, notify=changed)
    def rightMotorAvailable(self) -> bool:
        return bool(_read_object_value(self._wheel_controller, "right_motor_available", default=False))

    @Property(float, notify=changed)
    def leftWheelSpeed(self) -> float:
        value = _read_object_value(self._wheel_controller, "left_wheel_speed", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def rightWheelSpeed(self) -> float:
        value = _read_object_value(self._wheel_controller, "right_wheel_speed", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def leftWheelCurrent(self) -> float:
        value = _read_object_value(self._wheel_controller, "left_wheel_current", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def rightWheelCurrent(self) -> float:
        value = _read_object_value(self._wheel_controller, "right_wheel_current", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def leftWheelPosition(self) -> float:
        value = _read_object_value(self._wheel_controller, "left_wheel_position", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def rightWheelPosition(self) -> float:
        value = _read_object_value(self._wheel_controller, "right_wheel_position", default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0


class _TeensyStatus(QObject):
    changed = Signal()

    def __init__(self, teensy_controller: object) -> None:
        super().__init__()
        self._teensy_controller = teensy_controller
        _connect_if_signal(teensy_controller, "status_changed", self.changed.emit)

    def _status_value(self, key: str) -> Any:
        all_status = _read_object_value(self._teensy_controller, "all_status", default={})
        return _read_mapping_value(all_status, key)

    def _status_float(self, key: str) -> float:
        value = self._status_value(key)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _status_int(self, key: str) -> int:
        value = self._status_value(key)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @Property(bool, notify=changed)
    def enabled(self) -> bool:
        return bool(self._status_value("enabled"))

    @Property(bool, notify=changed)
    def relayOn(self) -> bool:
        return bool(self._status_value("relay_on"))

    @Property(float, notify=changed)
    def voltage(self) -> float:
        return self._status_float("voltage")

    @Property(float, notify=changed)
    def current(self) -> float:
        return self._status_float("current")

    @Property(float, notify=changed)
    def temperature(self) -> float:
        return self._status_float("temperature")

    @Property(float, notify=changed)
    def runTime(self) -> float:
        return self._status_float("run_time")

    @Property(float, notify=changed)
    def loopTime(self) -> float:
        return self._status_float("loop_time")

    @Property(float, notify=changed)
    def loopTimeCounter(self) -> float:
        return self._status_float("loop_time_counter")

    @Property(float, notify=changed)
    def imuPitch(self) -> float:
        return self._status_float("imu_pitch")

    @Property(float, notify=changed)
    def imuRoll(self) -> float:
        return self._status_float("imu_roll")

    @Property(float, notify=changed)
    def imuYaw(self) -> float:
        return self._status_float("imu_yaw")

    @Property(float, notify=changed)
    def yawCommand(self) -> float:
        return self._status_float("yaw_command")

    @Property(float, notify=changed)
    def yawPidP(self) -> float:
        return self._status_float("yaw_pid_p")

    @Property(float, notify=changed)
    def yawPidI(self) -> float:
        return self._status_float("yaw_pid_i")

    @Property(float, notify=changed)
    def yawPidD(self) -> float:
        return self._status_float("yaw_pid_d")

    @Property(float, notify=changed)
    def imuAccX(self) -> float:
        return self._status_float("imu_acc_x")

    @Property(float, notify=changed)
    def imuAccY(self) -> float:
        return self._status_float("imu_acc_y")

    @Property(float, notify=changed)
    def imuAccZ(self) -> float:
        return self._status_float("imu_acc_z")

    @Property(float, notify=changed)
    def imuAngularAccX(self) -> float:
        return self._status_float("imu_angular_acc_x")

    @Property(float, notify=changed)
    def imuAngularAccY(self) -> float:
        return self._status_float("imu_angular_acc_y")

    @Property(float, notify=changed)
    def imuAngularAccZ(self) -> float:
        return self._status_float("imu_angular_acc_z")

    @Property(float, notify=changed)
    def armExtensionDist(self) -> float:
        return self._status_float("arm_extension_dist")

    @Property(float, notify=changed)
    def armRailCurrent(self) -> float:
        return self._status_float("arm_rail_current")

    @Property(float, notify=changed)
    def gimbalPitchMotorCurrent(self) -> float:
        return self._status_float("gimbal_pitch_motor_current")

    @Property(float, notify=changed)
    def gimbalPitchMotorAngle(self) -> float:
        return self._status_float("gimbal_pitch_motor_angle")

    @Property(float, notify=changed)
    def topRailPosition(self) -> float:
        return self._status_float("top_rail_position")

    @Property(float, notify=changed)
    def topRailSpeed(self) -> float:
        return self._status_float("top_rail_speed")

    @Property(float, notify=changed)
    def topRailCurrent(self) -> float:
        return self._status_float("top_rail_current")

    @Property(float, notify=changed)
    def armRailPosition(self) -> float:
        return self._status_float("arm_rail_position")

    @Property(float, notify=changed)
    def armRailSpeed(self) -> float:
        return self._status_float("arm_rail_speed")

    @Property(float, notify=changed)
    def armSensorDist(self) -> float:
        return self._status_float("arm_sensor_dist")

    @Property(float, notify=changed)
    def leftPropPosition(self) -> float:
        return self._status_float("left_prop_position")

    @Property(float, notify=changed)
    def rightPropPosition(self) -> float:
        return self._status_float("right_prop_position")

    @Property(int, notify=changed)
    def leftPropPwm(self) -> int:
        return self._status_int("left_prop_pwm")

    @Property(int, notify=changed)
    def rightPropPwm(self) -> int:
        return self._status_int("right_prop_pwm")

    @Property(float, notify=changed)
    def sprayGunPitch(self) -> float:
        return self._status_float("spray_gun_pitch")

    @Property(float, notify=changed)
    def gimbalPitchMotorTemp(self) -> float:
        return self._status_float("gimbal_pitch_motor_temp")

    @Property(float, notify=changed)
    def gimbalRollMotorAngle(self) -> float:
        return self._status_float("gimbal_roll_motor_angle")

    @Property(float, notify=changed)
    def gimbalRollMotorCurrent(self) -> float:
        return self._status_float("gimbal_roll_motor_current")

    @Property(float, notify=changed)
    def gimbalRollMotorTemp(self) -> float:
        return self._status_float("gimbal_roll_motor_temp")

    @Property(bool, notify=changed)
    def sprayGunTrigger(self) -> bool:
        return bool(self._status_value("spray_gun_trigger"))

    @Property(bool, notify=changed)
    def stabilityEnabled(self) -> bool:
        return bool(_read_object_value(self._teensy_controller, "stability_enabled", default=False))

    @Property(bool, notify=changed)
    def yawEnabled(self) -> bool:
        return bool(self._status_value("yaw_enabled"))

    @Property(bool, notify=changed)
    def autoCorrectionEnabled(self) -> bool:
        return bool(_read_object_value(self._teensy_controller, "auto_correction_enabled", default=False))

    @Property(bool, notify=changed)
    def sprayGunLevelingEnabled(self) -> bool:
        return bool(_read_object_value(self._teensy_controller, "spray_gun_leveling_enabled", default=False))

    @Property(bool, notify=changed)
    def rollerSteeringEnabled(self) -> bool:
        return bool(_read_object_value(self._teensy_controller, "roller_steering_enabled", default=False))

    @Property(bool, notify=changed)
    def swingDampingEnabled(self) -> bool:
        return bool(_read_object_value(self._teensy_controller, "swing_damping_enabled", default=False))

    @Property(bool, notify=changed)
    def sprayGunLedOn(self) -> bool:
        return bool(_read_object_value(self._teensy_controller, "spray_gun_led_on", default=False))


class _ValveStatus(QObject):
    changed = Signal()

    def __init__(self, valve_controller: object) -> None:
        super().__init__()
        self._valve_controller = valve_controller
        for signal_name in (
            "valve_position_changed",
            "valve_rate_changed",
            "total_volume_changed",
            "valve_motor_current_changed",
            "valve_motor_connected_changed",
            "flow_meter_connected_changed",
            "esp32_connected_changed",
        ):
            _connect_if_signal(valve_controller, signal_name, self.changed.emit)

    def _float_value(self, key: str) -> float:
        value = _read_object_value(self._valve_controller, key, default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def valvePosition(self) -> float:
        return self._float_value("valve_position")

    @Property(float, notify=changed)
    def valveRate(self) -> float:
        return self._float_value("valve_rate")

    @Property(float, notify=changed)
    def totalVolume(self) -> float:
        return self._float_value("total_volume")

    @Property(float, notify=changed)
    def valveMotorCurrent(self) -> float:
        return self._float_value("valve_motor_current")

    @Property(bool, notify=changed)
    def valveMotorConnected(self) -> bool:
        return bool(_read_object_value(self._valve_controller, "valve_motor_connected", default=False))

    @Property(bool, notify=changed)
    def flowMeterConnected(self) -> bool:
        return bool(_read_object_value(self._valve_controller, "flow_meter_connected", default=False))

    @Property(bool, notify=changed)
    def connected(self) -> bool:
        return bool(_read_object_value(self._valve_controller, "esp32_connected", default=False))


class _LidarStatus(QObject):
    changed = Signal()

    def __init__(self, lidar_controller: object) -> None:
        super().__init__()
        self._lidar_controller = lidar_controller
        for signal_name in ("distance_changed", "angle_changed"):
            _connect_if_signal(lidar_controller, signal_name, self.changed.emit)

    def _float_value(self, key: str) -> float:
        value = _read_object_value(self._lidar_controller, key, default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=changed)
    def distance(self) -> float:
        return self._float_value("distance")

    @Property(float, notify=changed)
    def angle(self) -> float:
        return self._float_value("angle")


class _BaseTopViewStatus(QObject):
    changed = Signal()
    frameReady = Signal()

    def __init__(self, base_top_view_service: object) -> None:
        super().__init__()
        self._service = base_top_view_service
        for signal_name in (
            "zoomChanged",
            "offsetXChanged",
            "offsetYChanged",
            "cropEnabledChanged",
            "cropWidthRatioChanged",
            "cropCenterXChanged",
            "k1Changed",
            "k2Changed",
            "k3Changed",
            "k4Changed",
            "editModeChanged",
            "enabledChanged",
            "sourcePointsChanged",
        ):
            _connect_if_signal(base_top_view_service, signal_name, self.changed.emit)
        _connect_if_signal(base_top_view_service, "frameReady", self.frameReady.emit)

    def _float_value(self, key: str) -> float:
        value = _read_object_value(self._service, key, default=0.0)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(bool, notify=changed)
    def enabled(self) -> bool:
        return bool(_read_object_value(self._service, "enabled", default=False))

    @Property(bool, notify=changed)
    def editMode(self) -> bool:
        return bool(_read_object_value(self._service, "editMode", default=False))

    @Property(float, notify=changed)
    def zoom(self) -> float:
        return self._float_value("zoom")

    @Property(float, notify=changed)
    def offsetX(self) -> float:
        return self._float_value("offsetX")

    @Property(float, notify=changed)
    def offsetY(self) -> float:
        return self._float_value("offsetY")

    @Property(bool, notify=changed)
    def cropEnabled(self) -> bool:
        return bool(_read_object_value(self._service, "cropEnabled", default=False))

    @Property(float, notify=changed)
    def cropWidthRatio(self) -> float:
        return self._float_value("cropWidthRatio")

    @Property(float, notify=changed)
    def cropCenterX(self) -> float:
        return self._float_value("cropCenterX")

    @Property(float, notify=changed)
    def k1(self) -> float:
        return self._float_value("k1")

    @Property(float, notify=changed)
    def k2(self) -> float:
        return self._float_value("k2")

    @Property(float, notify=changed)
    def k3(self) -> float:
        return self._float_value("k3")

    @Property(float, notify=changed)
    def k4(self) -> float:
        return self._float_value("k4")

    @Property("QVariantList", notify=changed)
    def sourcePoints(self) -> Any:
        return _read_object_value(self._service, "sourcePoints", default=[])


class QmlContextComposer:
    """Builds the QML root-context property dict and the status wrappers it contains."""

    def __init__(self, runtime: AppRuntime) -> None:
        self._runtime = runtime

    def compose(self) -> dict[str, object]:
        """Create status wrappers and return the full context-property mapping."""
        runtime = self._runtime
        bundle = runtime.bundle
        if bundle is None:
            raise RuntimeError("ControllerBundle is required before composing QML context properties")

        system_control_services = _SystemControlServices(
            workflow_runner=bundle.workflow_runner,
            workflow_editor=bundle.workflow_editor,
            manual_command_handler=bundle.manual_command_handler,
        )
        video_runtime = _VideoRuntime(
            control_processor=bundle.control_processor,
            video_stream_handler=runtime.video_stream_handler,
            ssh_controller=bundle.ssh_controller,
            screen_recorder=bundle.screen_recorder,
            system_monitor=bundle.system_monitor,
            teensy_controller=bundle.teensy_controller,
            winch_controller=bundle.winch_controller,
        )
        recording_status = _RecordingStatus(
            video_stream_handler=runtime.video_stream_handler,
            screen_recorder=bundle.screen_recorder,
            ros_bag_recorder=bundle.ros_bag_recorder,
        )
        wheel_status = _WheelStatus(bundle.wheel_controller)
        winch_status = _WinchStatus(bundle.winch_controller)
        teensy_status = _TeensyStatus(bundle.teensy_controller)
        valve_status = _ValveStatus(bundle.esp32_valve_controller)
        lidar_status = _LidarStatus(bundle.lidar_controller)
        base_top_view_status = _BaseTopViewStatus(runtime.base_top_view_service)
        shell_connectivity_status = _ShellConnectivityStatus(
            ssh_controller=bundle.ssh_controller,
            heartbeat_handler=bundle.heartbeat_handler,
            winch_controller=bundle.winch_controller,
            wheel_status=wheel_status,
            teensy_controller=bundle.teensy_controller,
        )
        launcher_admin = _LauncherAdmin(bundle.ssh_controller)

        return {
            "stateStore": runtime.state_store,
            "backend": runtime.qt_bridge,
            "shellState": runtime.shell_state,
            "overlayHost": runtime.overlay_host,
            "actionLegality": runtime.action_legality,
            "systemControlServices": system_control_services,
            "videoRuntime": video_runtime,
            "recordingStatus": recording_status,
            "recordingActions": bundle.recording_actions,
            "wheelStatus": wheel_status,
            "wheelActions": bundle.wheel_actions,
            "teensyActions": bundle.teensy_actions,
            "systemActions": bundle.system_actions,
            "winchStatus": winch_status,
            "teensyStatus": teensy_status,
            "valveStatus": valve_status,
            "lidarStatus": lidar_status,
            "shellConnectivityStatus": shell_connectivity_status,
            "launcherAdmin": launcher_admin,
            "overlayController": bundle.overlay_controller,
            "warningHandler": bundle.warning_handler,
            "deviceActionHandler": bundle.device_action_handler,
            "winchActions": bundle.winch_actions,
            "tuningActions": bundle.tuning_actions,
            "baseTopViewActions": bundle.base_top_view_actions,
            "baseTopViewStatus": base_top_view_status,
            "shellRouter": runtime.shell_router,
            "settingsManager": runtime.settings_manager,
        }


def compose_context_properties(runtime: AppRuntime) -> dict[str, object]:
    """Convenience entry point matching the master-plan function signature."""
    return QmlContextComposer(runtime).compose()
