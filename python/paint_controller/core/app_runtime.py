"""Application runtime orchestration for the paint controller."""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from typing import Any

import rclpy
from PySide6.QtCore import Property, QCoreApplication, QEvent, QObject, QTimer, QUrl, Qt, Signal
from PySide6.QtCore import Slot
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from paint_controller.core.config import RuntimeDefaults
from paint_controller.core.ros_node import RosThread
from paint_controller.core.settings import SettingsManager
from paint_controller.handlers.steam_deck import SteamDeckHandler
from paint_controller.models.action_legality_model import ActionLegalityModel
from paint_controller.models.capability_catalog import CapabilityCatalog
from paint_controller.services.base_top_view_service import BaseTopViewService
from paint_controller.services.video_stream import VideoStreamHandler
from paint_controller.utils.qt_env import ensure_pyside6_windows_dll_path

logger = logging.getLogger(__name__)

_EXPECTED_CONTEXT_PROPERTY_NAMES = (
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
    "baseStreamHandler",
    "wheelController",
    "winchController",
    "teensyController",
    "esp32ValveController",
    "lidarController",
    "controlProcessor",
    "deviceActionHandler",
    "deviceOperationsHandler",
    "winchMotionHandler",
    "tuningAdminHandler",
    "baseTopViewAdminHandler",
    "systemMonitor",
    "screenRecorder",
    "rosBagRecorder",
    "settingsManager",
    "screenManager",
    "baseTopViewController",
)


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


def _connect_if_signal(owner: object, signal_name: str, callback: Callable[..., None]) -> None:
    signal = getattr(owner, signal_name, None)
    if signal is None or not hasattr(signal, "connect"):
        return
    signal.connect(lambda *_args, **_kwargs: callback())


def _read_mapping_value(mapping: object, key: str) -> Any:
    if isinstance(mapping, dict):
        return mapping.get(key)
    if hasattr(mapping, "property"):
        value = mapping.property(key)
        if value is not None:
            return value
    return getattr(mapping, key, None)


def _read_object_value(owner: object, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(owner, name):
            return getattr(owner, name)
        if hasattr(owner, "property"):
            value = owner.property(name)
            if value is not None:
                return value
    return default


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


def teardown_qml_runtime(
    engine: QQmlApplicationEngine,
    app: QApplication,
    log_shutdown,
) -> None:
    """Destroy QML root objects before backend QObject cleanup begins."""
    try:
        root_objects = list(engine.rootObjects())

        for root in root_objects:
            try:
                close = getattr(root, "close", None)
                if callable(close):
                    close()
            except Exception as exc:
                logger.debug("Error closing QML root object: %s", exc)

        for root in root_objects:
            try:
                root.deleteLater()
            except Exception as exc:
                logger.debug("Error deleting QML root object: %s", exc)

        engine.clearComponentCache()
        engine.deleteLater()

        for _ in range(5):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            app.processEvents()

        log_shutdown(f"QML runtime torn down ({len(root_objects)} root object(s))")
    except Exception as exc:
        logger.error("Error tearing down QML runtime: %s", exc)


class AppRuntime:
    """Own startup wiring, event-loop execution, and shutdown sequencing."""

    def __init__(self, argv: list[str], on_app_created: Callable[[QApplication], None] | None = None):
        self.argv = list(argv)
        self._on_app_created = on_app_created
        self.config = RuntimeDefaults()
        self._startup_t0 = time.perf_counter()
        self._shutdown_started = False
        self._context_properties: dict[str, object] = {}
        self._heartbeat_status_error = None

        self.app: QApplication | None = None
        self.state_store = None
        self.node = None
        self.settings_manager: SettingsManager | None = None
        self.capability_catalog: CapabilityCatalog | None = None
        self.steam_deck_handler: SteamDeckHandler | None = None
        self.video_stream_handler: VideoStreamHandler | None = None
        self.base_top_view_service: BaseTopViewService | None = None
        self.ros_thread: RosThread | None = None
        self.engine: QQmlApplicationEngine | None = None
        self.qt_bridge = None
        self.bundle = None
        self.system_control_services: _SystemControlServices | None = None
        self.video_runtime: _VideoRuntime | None = None
        self.recording_status: _RecordingStatus | None = None
        self.wheel_status: _WheelStatus | None = None
        self.winch_status: _WinchStatus | None = None
        self.teensy_status: _TeensyStatus | None = None
        self.valve_status: _ValveStatus | None = None
        self.lidar_status: _LidarStatus | None = None
        self.shell_connectivity_status: _ShellConnectivityStatus | None = None
        self.launcher_admin: _LauncherAdmin | None = None
        self.shell_state = None
        self.overlay_host = None
        self.action_legality = None
        self.status_timer: QTimer | None = None
        self.qml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qml')

        try:
            self._bootstrap()
        except Exception:
            self.shutdown()
            raise

    def _log_startup(self, stage: str) -> None:
        elapsed_ms = (time.perf_counter() - self._startup_t0) * 1000.0
        logger.warning("[startup +%7.1f ms] %s", elapsed_ms, stage)

    def _bootstrap(self) -> None:
        rclpy.init()
        self._log_startup("ROS initialized")
        self._log_startup("Runtime defaults loaded")

        ensure_pyside6_windows_dll_path()

        self.app = QApplication(self.argv)
        if self._on_app_created is not None:
            self._on_app_created(self.app)
        self._log_startup("QApplication created")

        self._setup_core_objects()
        self._setup_video_services()

        assert self.steam_deck_handler is not None
        self.steam_deck_handler.start()
        self._log_startup("Steam Deck handler started")

        assert self.node is not None
        self.ros_thread = RosThread(self.node)
        self.ros_thread.start()
        self._log_startup("ROS thread started")

        self._setup_qml_engine()
        self._create_controller_bundle()
        self._wire_steam_deck_callbacks()
        self._wire_signals()
        self._register_context_properties()
        self._load_qml()
        self._start_timers()

    def _setup_core_objects(self) -> None:
        from paint_controller.core.ros_node import PaintRosNode
        from paint_controller.core.state_store import StateStore

        self.state_store = StateStore()
        self.node = PaintRosNode(state_store=self.state_store)
        self._log_startup("PaintRosNode created")

        self.settings_manager = SettingsManager(show_popup_fn=None)
        self.capability_catalog = CapabilityCatalog(settings_manager=self.settings_manager)
        self.steam_deck_handler = SteamDeckHandler(deadzone=self.config.joystick_deadzone)
        self._log_startup("Core state/services created")

    def _setup_video_services(self) -> None:
        assert self.node is not None
        assert self.settings_manager is not None

        self.video_stream_handler = VideoStreamHandler(self.config.video_port, ros_node=self.node)
        self.base_top_view_service = BaseTopViewService(
            self.video_stream_handler,
            settings_manager=self.settings_manager,
        )
        self._log_startup("Video and camera services created")

    def _setup_qml_engine(self) -> None:
        from paint_controller.core.qt_bridge import QtBridge

        assert self.node is not None
        assert self.state_store is not None
        assert self.video_stream_handler is not None
        assert self.base_top_view_service is not None

        self.engine = QQmlApplicationEngine()
        self.engine.addImageProvider("ef_live", self.video_stream_handler.ef_image_provider)
        self.engine.addImageProvider("base_front_live", self.video_stream_handler.front_image_provider)
        self.engine.addImageProvider("base_rear_live", self.video_stream_handler.rear_image_provider)
        self.engine.addImageProvider("base_top_view", self.base_top_view_service.image_provider)
        self._log_startup("QML engine and image providers ready")

        self.engine.addImportPath(self.qml_dir)
        self.qt_bridge = QtBridge(self.engine, self.state_store, logger=self.node.get_logger())
        self._log_startup("Qt bridge created")

        assert self.settings_manager is not None
        self.settings_manager._show_popup_fn = self.qt_bridge.show_popup

    def _create_controller_bundle(self) -> None:
        from paint_controller.core.controller_factory import create_controllers
        from paint_controller.models.overlay_host_policy import OverlayHostPolicy
        from paint_controller.models.shell_state import ShellState

        assert self.node is not None
        assert self.settings_manager is not None
        assert self.state_store is not None
        assert self.steam_deck_handler is not None
        assert self.qt_bridge is not None
        assert self.base_top_view_service is not None

        self.bundle = create_controllers(
            node=self.node,
            settings_manager=self.settings_manager,
            capability_catalog=self.capability_catalog,
            state_store=self.state_store,
            steam_deck_handler=self.steam_deck_handler,
            video_stream_handler=self.video_stream_handler,
            base_top_view_service=self.base_top_view_service,
            show_popup_fn=self.qt_bridge.show_popup,
            close_popup_fn=self.qt_bridge.close_popup,
        )
        self._log_startup("Controller bundle created")

        self.qt_bridge.set_base_top_view_service(self.base_top_view_service)
        self.qt_bridge.set_input_handler(self.bundle.input_handler)
        self.shell_state = ShellState(screen_manager=self.bundle.screen_manager)
        self.overlay_host = OverlayHostPolicy(shell_state=self.shell_state)
        self.action_legality = ActionLegalityModel(
            admin_action_gate=self.bundle.admin_action_gate,
            capability_catalog=self.capability_catalog,
        )
        self.system_control_services = _SystemControlServices(
            workflow_runner=self.bundle.workflow_runner,
            workflow_editor=self.bundle.workflow_editor,
            manual_command_handler=self.bundle.manual_command_handler,
        )
        self.video_runtime = _VideoRuntime(
            control_processor=self.bundle.control_processor,
            video_stream_handler=self.video_stream_handler,
            ssh_controller=self.bundle.ssh_controller,
            screen_recorder=self.bundle.screen_recorder,
            system_monitor=self.bundle.system_monitor,
            teensy_controller=self.bundle.teensy_controller,
            winch_controller=self.bundle.winch_controller,
        )
        self.recording_status = _RecordingStatus(
            video_stream_handler=self.video_stream_handler,
            screen_recorder=self.bundle.screen_recorder,
            ros_bag_recorder=self.bundle.ros_bag_recorder,
        )
        self.wheel_status = _WheelStatus(self.bundle.wheel_controller)
        self.winch_status = _WinchStatus(self.bundle.winch_controller)
        self.teensy_status = _TeensyStatus(self.bundle.teensy_controller)
        self.valve_status = _ValveStatus(self.bundle.esp32_valve_controller)
        self.lidar_status = _LidarStatus(self.bundle.lidar_controller)
        self.shell_connectivity_status = _ShellConnectivityStatus(
            ssh_controller=self.bundle.ssh_controller,
            heartbeat_handler=self.bundle.heartbeat_handler,
            winch_controller=self.bundle.winch_controller,
            wheel_status=self.wheel_status,
            teensy_controller=self.bundle.teensy_controller,
        )
        self.launcher_admin = _LauncherAdmin(self.bundle.ssh_controller)

    def _wire_steam_deck_callbacks(self) -> None:
        assert self.bundle is not None
        assert self.steam_deck_handler is not None
        assert self.qt_bridge is not None

        input_handler = self.bundle.input_handler
        self.steam_deck_handler.register_button_callback('up', input_handler.on_up_pressed)
        self.steam_deck_handler.register_button_callback('down', input_handler.on_down_pressed)
        self.steam_deck_handler.register_button_callback('left', input_handler.on_left_pressed)
        self.steam_deck_handler.register_button_callback('right', input_handler.on_right_pressed)
        self.steam_deck_handler.register_button_callback('r4', input_handler.on_r4_pressed)
        self.steam_deck_handler.register_button_callback('l4', input_handler.on_l4_pressed)
        self.steam_deck_handler.register_button_callback('menu', input_handler.on_menu_pressed)
        self.steam_deck_handler.register_button_callback('switch', input_handler.on_switch_pressed)
        self.steam_deck_handler.register_button_callback('l5', input_handler.on_l5_pressed)
        self.steam_deck_handler.register_button_callback('r5', input_handler.on_r5_pressed)
        self.steam_deck_handler.register_button_callback('dot', self.qt_bridge.toggle_fullscreen)
        self.steam_deck_handler.register_button_callback('a', self.qt_bridge.toggle_lidar_overlay)
        self.steam_deck_handler.register_button_callback('l1', input_handler.on_l1_pressed)

    def _wire_signals(self) -> None:
        from paint_controller.utils.constants import HeartbeatStatus

        assert self.bundle is not None
        assert self.node is not None
        assert self.qt_bridge is not None
        assert self.state_store is not None
        assert self.video_stream_handler is not None
        assert self.steam_deck_handler is not None
        assert self.overlay_host is not None
        assert self.video_runtime is not None

        self._heartbeat_status_error = HeartbeatStatus.ERROR
        self.state_store.control_mode_changed.connect(self.qt_bridge.update_fullscreen_video_source)
        self.bundle.emergency_handler.overlay_changed.connect(self.qt_bridge.emergency_overlay_changed.emit)
        self.bundle.emergency_handler.emergency_triggered.connect(self.qt_bridge.emergency_triggered.emit)
        self.video_stream_handler.endEffectorFrameReady.connect(self.qt_bridge.frame_ready.emit)
        self.bundle.wheel_controller.error_state_changed.connect(
            self._on_wheel_motor_error,
            Qt.QueuedConnection,
        )
        self.qt_bridge.status_updated.connect(self._on_status_tick)

        self.video_runtime.topBar.endEffectorVideoRequested.connect(
            lambda: self.overlay_host.set_video_fullscreen_source("image://ef_live/frame")
        )
        self.video_runtime.topBar.baseVideoRequested.connect(
            lambda: self.overlay_host.set_video_fullscreen_source("image://base_front_live/frame")
        )

    def _on_wheel_motor_error(self, has_error, error_message) -> None:
        if not has_error:
            return

        assert self.bundle is not None
        assert self.node is not None
        assert self.qt_bridge is not None

        self.node.get_logger().error(f'Wheel motor error detected: {error_message}')
        self.bundle.safety_coordinator.halt_all_effectors(
            f"Wheel motor error detected: {error_message}",
            heartbeat_state=self._heartbeat_status_error,
        )
        self.qt_bridge.show_popup("MOTOR ERROR", error_message, "error", 5000)
        self.qt_bridge.emergency_triggered.emit()

    def _on_status_tick(self) -> None:
        assert self.bundle is not None
        assert self.steam_deck_handler is not None

        input_state = self.steam_deck_handler.get_current_state()
        self.bundle.control_processor.process_input(input_state)
        self.bundle.emergency_handler.check_emergency_button(input_state.get('buttons', {}))

    def _build_context_properties(self) -> dict[str, object]:
        assert self.bundle is not None
        assert self.state_store is not None
        assert self.qt_bridge is not None
        assert self.shell_state is not None
        assert self.overlay_host is not None
        assert self.action_legality is not None
        assert self.system_control_services is not None
        assert self.video_runtime is not None
        assert self.recording_status is not None
        assert self.wheel_status is not None
        assert self.winch_status is not None
        assert self.teensy_status is not None
        assert self.valve_status is not None
        assert self.lidar_status is not None
        assert self.shell_connectivity_status is not None
        assert self.launcher_admin is not None
        assert self.video_stream_handler is not None
        assert self.steam_deck_handler is not None
        assert self.settings_manager is not None
        assert self.capability_catalog is not None
        assert self.base_top_view_service is not None

        return {
            "stateStore": self.state_store,
            "backend": self.qt_bridge,
            "shellState": self.shell_state,
            "overlayHost": self.overlay_host,
            "actionLegality": self.action_legality,
            "systemControlServices": self.system_control_services,
            "videoRuntime": self.video_runtime,
            "recordingStatus": self.recording_status,
            "wheelStatus": self.wheel_status,
            "winchStatus": self.winch_status,
            "teensyStatus": self.teensy_status,
            "valveStatus": self.valve_status,
            "lidarStatus": self.lidar_status,
            "shellConnectivityStatus": self.shell_connectivity_status,
            "launcherAdmin": self.launcher_admin,
            "overlayController": self.bundle.overlay_controller,
            "warningHandler": self.bundle.warning_handler,
            "baseStreamHandler": self.video_stream_handler,
            "wheelController": self.bundle.wheel_controller,
            "winchController": self.bundle.winch_controller,
            "teensyController": self.bundle.teensy_controller,
            "esp32ValveController": self.bundle.esp32_valve_controller,
            "lidarController": self.bundle.lidar_controller,
            "controlProcessor": self.bundle.control_processor,
            "deviceActionHandler": self.bundle.device_action_handler,
            "deviceOperationsHandler": self.bundle.device_operations_handler,
            "winchMotionHandler": self.bundle.winch_motion_handler,
            "tuningAdminHandler": self.bundle.tuning_admin_handler,
            "baseTopViewAdminHandler": self.bundle.base_top_view_admin_handler,
            "systemMonitor": self.bundle.system_monitor,
            "screenRecorder": self.bundle.screen_recorder,
            "rosBagRecorder": self.bundle.ros_bag_recorder,
            "settingsManager": self.settings_manager,
            "screenManager": self.bundle.screen_manager,
            "baseTopViewController": self.base_top_view_service,
        }

    def _register_context_properties(self) -> None:
        assert self.engine is not None
        assert self.node is not None

        context = self.engine.rootContext()
        self._context_properties = self._build_context_properties()
        expected_names = set(_EXPECTED_CONTEXT_PROPERTY_NAMES)
        actual_names = set(self._context_properties)

        missing_names = sorted(expected_names - actual_names)
        unexpected_names = sorted(actual_names - expected_names)
        if missing_names or unexpected_names:
            self.node.get_logger().error(
                f"Context-property contract mismatch. Missing: {missing_names}; unexpected: {unexpected_names}"
            )

        for name, obj in self._context_properties.items():
            context.setContextProperty(name, obj)

    def _load_qml(self) -> None:
        assert self.engine is not None
        assert self.node is not None

        qml_path = os.path.join(self.qml_dir, 'core', 'MainWindow.qml')
        self.engine.load(QUrl.fromLocalFile(qml_path))
        if not self.engine.rootObjects():
            raise RuntimeError(f"Failed to load QML root: {qml_path}")
        self._log_startup("MainWindow QML loaded")

        context = self.engine.rootContext()
        for name in _EXPECTED_CONTEXT_PROPERTY_NAMES:
            if context.contextProperty(name) is None:
                self.node.get_logger().error(f"Missing QML context property: {name}")

    def _start_timers(self) -> None:
        assert self.bundle is not None
        assert self.qt_bridge is not None

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.qt_bridge.status_updated.emit)
        self.status_timer.start(int(1000 / self.config.update_rate))
        self._log_startup("Status timer started")

        self.bundle.system_monitor.start_monitoring(interval_ms=1000)
        self._log_startup("System monitoring started")

        QTimer.singleShot(200, self._deferred_video_startup)
        self._log_startup("Deferred video startup scheduled")

    def _deferred_video_startup(self) -> None:
        assert self.video_stream_handler is not None

        self._log_startup("Deferred video startup begin")
        started_count = self.video_stream_handler.start_all_streams()
        self._log_startup(f"Deferred video startup end: started {started_count} stream(s)")

    def exec(self) -> int:
        assert self.app is not None
        self._log_startup("Entering Qt event loop")
        return self.app.exec()

    def shutdown(self) -> None:
        if self._shutdown_started:
            return
        self._shutdown_started = True

        shutdown_t0 = time.perf_counter()

        def log_shutdown(stage: str) -> None:
            elapsed_ms = (time.perf_counter() - shutdown_t0) * 1000.0
            logger.warning("[shutdown +%7.1f ms] %s", elapsed_ms, stage)

        logger.info("Starting emergency shutdown sequence...")
        log_shutdown("Shutdown sequence started")

        try:
            if self.status_timer is not None:
                self.status_timer.stop()
            log_shutdown("Qt timers stopped")
        except Exception as error:
            logger.error("Error stopping timers: %s", error)

        if self.engine is not None and self.app is not None:
            teardown_qml_runtime(self.engine, self.app, log_shutdown)
            self.engine = None

        try:
            if self.ros_thread is not None:
                self.ros_thread.request_shutdown()
                if not self.ros_thread.wait(2000):
                    logger.warning("ROS thread did not exit cleanly, forcing termination...")
                    self.ros_thread.terminate()
                    self.ros_thread.wait(500)
            log_shutdown("ROS thread stopped")
        except Exception as error:
            logger.error("Error shutting down ROS thread: %s", error)

        try:
            if self.bundle is not None and self.node is not None:
                self.bundle.cleanup(self.node.get_logger())
                log_shutdown("Controller bundle cleaned up")
            if self.base_top_view_service is not None:
                self.base_top_view_service.cleanup()
                log_shutdown("Base top view service cleaned up")
            if self.video_stream_handler is not None:
                self.video_stream_handler.cleanup()
                log_shutdown("Video stream handler cleaned up")
            if self.steam_deck_handler is not None:
                self.steam_deck_handler.cleanup()
                log_shutdown("Steam Deck handler cleaned up")
        except Exception as error:
            logger.error("Error during cleanup: %s", error)

        try:
            if self.node is not None:
                self.node.cleanup()
                self.node.destroy_node()
                log_shutdown("ROS node cleaned up and destroyed")
        except Exception as error:
            logger.error("Error during ROS node cleanup: %s", error)

        try:
            if rclpy.ok():
                rclpy.shutdown()
            log_shutdown("ROS context shutdown complete")
        except Exception as error:
            logger.error("Error during ROS shutdown: %s", error)

        logger.info("Emergency shutdown sequence complete")
