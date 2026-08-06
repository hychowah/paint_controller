"""Compose the QML root-context property dict and status wrappers."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from paint_controller.models.lidar_status import LidarStatus
from paint_controller.models.teensy_status import TeensyStatus
from paint_controller.models.valve_status import ValveStatus
from paint_controller.models.wheel_status import WheelStatus
from paint_controller.models.winch_status import WinchStatus

logger = logging.getLogger(__name__)


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
        return str(_read_object_value(self._control_processor, "left_control_mode_display", default=""))

    @Property(str, notify=changed)
    def rightModeDisplay(self) -> str:
        return str(_read_object_value(self._control_processor, "right_control_mode_display", default=""))


class _VideoRuntimeFeeds(QObject):
    """QML-facing feed signals/properties; liveness policy lives on VideoStreamHandler."""

    endEffectorFrameReady = Signal()
    baseFrontFrameReady = Signal()
    baseRearFrameReady = Signal()
    endEffectorStreamAvailableChanged = Signal()
    baseFrontStreamAvailableChanged = Signal()
    baseRearStreamAvailableChanged = Signal()
    endEffectorFrameGenerationChanged = Signal()
    baseFrontFrameGenerationChanged = Signal()
    baseRearFrameGenerationChanged = Signal()

    def __init__(self, video_stream_handler: object) -> None:
        super().__init__()
        self._video_stream_handler = video_stream_handler
        _connect_if_signal(video_stream_handler, "endEffectorFrameReady", self.endEffectorFrameReady.emit)
        _connect_if_signal(video_stream_handler, "baseFrontFrameReady", self.baseFrontFrameReady.emit)
        _connect_if_signal(video_stream_handler, "baseRearFrameReady", self.baseRearFrameReady.emit)
        _connect_if_signal(
            video_stream_handler,
            "endEffectorStreamAvailableChanged",
            self.endEffectorStreamAvailableChanged.emit,
        )
        _connect_if_signal(
            video_stream_handler,
            "baseFrontStreamAvailableChanged",
            self.baseFrontStreamAvailableChanged.emit,
        )
        _connect_if_signal(
            video_stream_handler,
            "baseRearStreamAvailableChanged",
            self.baseRearStreamAvailableChanged.emit,
        )
        _connect_if_signal(
            video_stream_handler,
            "endEffectorFrameGenerationChanged",
            self.endEffectorFrameGenerationChanged.emit,
        )
        _connect_if_signal(
            video_stream_handler,
            "baseFrontFrameGenerationChanged",
            self.baseFrontFrameGenerationChanged.emit,
        )
        _connect_if_signal(
            video_stream_handler,
            "baseRearFrameGenerationChanged",
            self.baseRearFrameGenerationChanged.emit,
        )

    @Property(bool, notify=endEffectorStreamAvailableChanged)
    def endEffectorStreamAvailable(self) -> bool:
        return bool(
            _read_object_value(self._video_stream_handler, "endEffectorStreamAvailable", default=False)
        )

    @Property(bool, notify=baseFrontStreamAvailableChanged)
    def baseFrontStreamAvailable(self) -> bool:
        return bool(
            _read_object_value(self._video_stream_handler, "baseFrontStreamAvailable", default=False)
        )

    @Property(bool, notify=baseRearStreamAvailableChanged)
    def baseRearStreamAvailable(self) -> bool:
        return bool(
            _read_object_value(self._video_stream_handler, "baseRearStreamAvailable", default=False)
        )

    @Property(int, notify=endEffectorFrameGenerationChanged)
    def endEffectorFrameGeneration(self) -> int:
        return int(
            _read_object_value(self._video_stream_handler, "endEffectorFrameGeneration", default=0)
        )

    @Property(int, notify=baseFrontFrameGenerationChanged)
    def baseFrontFrameGeneration(self) -> int:
        return int(
            _read_object_value(self._video_stream_handler, "baseFrontFrameGeneration", default=0)
        )

    @Property(int, notify=baseRearFrameGenerationChanged)
    def baseRearFrameGeneration(self) -> int:
        return int(
            _read_object_value(self._video_stream_handler, "baseRearFrameGeneration", default=0)
        )

    @Slot(str, int, result=str)
    def versionedImageUrl(self, base_url: str, generation: int) -> str:
        """Build image:// URL with generation query (P-01); no empty-source thrash."""
        return _versioned_image_url(base_url, generation)


def _versioned_image_url(base_url: str, generation: int) -> str:
    """Pure helper for tests and :meth:`_VideoRuntimeFeeds.versionedImageUrl`."""
    base = str(base_url or "").split("?", 1)[0]
    if not base:
        return ""
    return f"{base}?g={int(generation)}"


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
            (
                system_monitor,
                (
                    "battery_level_changed",
                    "battery_remaining_time_changed",
                    "cpu_temperature_changed",
                ),
            ),
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
            (
                ros_bag_recorder,
                (
                    "is_bag_recording_changed",
                    "bag_recording_duration_changed",
                    "is_compressing_changed",
                    "bag_status_message_changed",
                ),
            ),
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
            (
                heartbeat_handler,
                (
                    "base_online_changed",
                    "base_status_changed",
                    "ef_online_changed",
                    "ef_status_changed",
                ),
            ),
            (winch_controller, ("available_changed",)),
            # WheelStatus (TD-037) uses per-property notifies; availability is the shell need.
            (wheel_status, ("availableChanged",)),
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


@dataclass(frozen=True)
class QmlComposePorts:
    """Dependencies QmlContextComposer needs — no AppRuntime service locator (TD-047)."""

    bundle: Any
    video_stream_handler: Any
    base_top_view_service: Any
    qt_bridge: Any
    shell_state: Any
    shell_router: Any
    overlay_host: Any
    action_legality: Any
    settings_manager: Any


@dataclass(frozen=True)
class ContextProp:
    """Base entry for a QML root-context property."""

    name: str


@dataclass(frozen=True)
class BundleProp(ContextProp):
    """Passthrough property read from ``ControllerBundle``."""

    field: str


@dataclass(frozen=True)
class PortsProp(ContextProp):
    """Passthrough property read from ``QmlComposePorts``."""

    field: str


@dataclass(frozen=True)
class WrapperProp(ContextProp):
    """Property built from a factory callable receiving ``QmlComposePorts``."""

    builder: Callable[[QmlComposePorts], object]


def _wheel_status_builder(ports: QmlComposePorts) -> WheelStatus:
    return WheelStatus(ports.bundle.wheel_controller)


def _winch_status_builder(ports: QmlComposePorts) -> WinchStatus:
    return WinchStatus(ports.bundle.winch_controller)


def _teensy_status_builder(ports: QmlComposePorts) -> TeensyStatus:
    return TeensyStatus(ports.bundle.teensy_controller)


def _valve_status_builder(ports: QmlComposePorts) -> ValveStatus:
    return ValveStatus(ports.bundle.esp32_valve_controller)


def _lidar_status_builder(ports: QmlComposePorts) -> LidarStatus:
    return LidarStatus(ports.bundle.lidar_controller)


def _system_control_services_builder(ports: QmlComposePorts) -> _SystemControlServices:
    bundle = ports.bundle
    return _SystemControlServices(
        workflow_runner=bundle.workflow_runner,
        workflow_editor=bundle.workflow_editor,
        manual_command_handler=bundle.manual_command_handler,
    )


def _video_runtime_builder(ports: QmlComposePorts) -> _VideoRuntime:
    bundle = ports.bundle
    return _VideoRuntime(
        control_processor=bundle.control_processor,
        video_stream_handler=ports.video_stream_handler,
        ssh_controller=bundle.ssh_controller,
        screen_recorder=bundle.screen_recorder,
        system_monitor=bundle.system_monitor,
        teensy_controller=bundle.teensy_controller,
        winch_controller=bundle.winch_controller,
    )


def _recording_status_builder(ports: QmlComposePorts) -> _RecordingStatus:
    bundle = ports.bundle
    return _RecordingStatus(
        video_stream_handler=ports.video_stream_handler,
        screen_recorder=bundle.screen_recorder,
        ros_bag_recorder=bundle.ros_bag_recorder,
    )


def _base_top_view_status_builder(ports: QmlComposePorts) -> _BaseTopViewStatus:
    return _BaseTopViewStatus(ports.base_top_view_service)


def _shell_connectivity_status_builder(ports: QmlComposePorts) -> _ShellConnectivityStatus:
    bundle = ports.bundle
    return _ShellConnectivityStatus(
        ssh_controller=bundle.ssh_controller,
        heartbeat_handler=bundle.heartbeat_handler,
        winch_controller=bundle.winch_controller,
        wheel_status=_wheel_status_builder(ports),
        teensy_controller=bundle.teensy_controller,
    )


def _launcher_admin_builder(ports: QmlComposePorts) -> _LauncherAdmin:
    return _LauncherAdmin(ports.bundle.ssh_controller)


CONTEXT_PROPERTIES: tuple[ContextProp, ...] = (
    PortsProp("qtBridge", "qt_bridge"),
    PortsProp("shellState", "shell_state"),
    PortsProp("overlayHost", "overlay_host"),
    PortsProp("actionLegality", "action_legality"),
    WrapperProp("systemControlServices", _system_control_services_builder),
    WrapperProp("videoRuntime", _video_runtime_builder),
    WrapperProp("recordingStatus", _recording_status_builder),
    BundleProp("recordingActions", "recording_actions"),
    WrapperProp("wheelStatus", _wheel_status_builder),
    BundleProp("wheelActions", "wheel_actions"),
    BundleProp("teensyActions", "teensy_actions"),
    BundleProp("systemActions", "system_actions"),
    WrapperProp("winchStatus", _winch_status_builder),
    WrapperProp("teensyStatus", _teensy_status_builder),
    WrapperProp("valveStatus", _valve_status_builder),
    WrapperProp("lidarStatus", _lidar_status_builder),
    WrapperProp("shellConnectivityStatus", _shell_connectivity_status_builder),
    WrapperProp("launcherAdmin", _launcher_admin_builder),
    BundleProp("overlayController", "overlay_controller"),
    BundleProp("warningHandler", "warning_handler"),
    BundleProp("winchActions", "winch_actions"),
    BundleProp("tuningActions", "tuning_actions"),
    BundleProp("baseTopViewActions", "base_top_view_actions"),
    WrapperProp("baseTopViewStatus", _base_top_view_status_builder),
    PortsProp("shellRouter", "shell_router"),
    PortsProp("settingsManager", "settings_manager"),
)

_EXPECTED_CONTEXT_PROPERTY_NAMES: tuple[str, ...] = tuple(prop.name for prop in CONTEXT_PROPERTIES)


class QmlContextComposer:
    """Builds the QML root-context property dict and the status wrappers it contains."""

    def __init__(self, ports: QmlComposePorts) -> None:
        self._ports = ports

    def compose(self) -> dict[str, object]:
        """Create status wrappers and return the full context-property mapping."""
        ports = self._ports
        if ports.bundle is None:
            raise RuntimeError("ControllerBundle is required before composing QML context properties")

        properties: dict[str, object] = {}
        for prop in CONTEXT_PROPERTIES:
            if isinstance(prop, BundleProp):
                properties[prop.name] = getattr(ports.bundle, prop.field)
            elif isinstance(prop, PortsProp):
                properties[prop.name] = getattr(ports, prop.field)
            elif isinstance(prop, WrapperProp):
                properties[prop.name] = prop.builder(ports)
            else:  # pragma: no cover - defensive guard
                raise TypeError(f"Unknown context-property kind: {type(prop).__name__}")
        return properties
