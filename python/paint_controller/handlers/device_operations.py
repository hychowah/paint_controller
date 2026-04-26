"""Python-owned device and operational side-effect boundary for the system-control overlay."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class DeviceOperationsHandler(QObject):
    """Own non-joystick device toggles and recorder operations initiated from QML."""

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: Any,
        winch: Any,
        video_stream_handler: Any,
        screen_recorder: Any,
        ros_bag_recorder: Any,
        heartbeat_handler: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._winch = winch
        self._video_stream_handler = video_stream_handler
        self._screen_recorder = screen_recorder
        self._ros_bag_recorder = ros_bag_recorder
        self._heartbeat_handler = heartbeat_handler
        self._logger = logger

    @Slot(bool, result=bool)
    def toggleLoadDetection(self, current_enabled: bool) -> bool:
        return self._run_toggle(
            name="Load detection",
            controller=self._winch,
            method_name="setLoadDetectionEnabled",
            next_enabled=not current_enabled,
        )

    @Slot(result=bool)
    def toggleEndEffectorRecording(self) -> bool:
        return self._run_action(
            name="EF camera recording",
            controller=self._video_stream_handler,
            method_name="toggleRecording",
        )

    @Slot(result=bool)
    def toggleBaseRecording(self) -> bool:
        return self._run_action(
            name="Base camera recording",
            controller=self._video_stream_handler,
            method_name="toggleBaseRecording",
        )

    @Slot(result=bool)
    def toggleScreenRecording(self) -> bool:
        return self._run_action(
            name="Screen recording",
            controller=self._screen_recorder,
            method_name="toggleRecording",
        )

    @Slot(result=bool)
    def toggleRosBagRecording(self) -> bool:
        return self._run_action(
            name="ROS bag recording",
            controller=self._ros_bag_recorder,
            method_name="toggleBagRecording",
        )

    @Slot(bool, result=bool)
    def toggleStability(self, current_enabled: bool) -> bool:
        return self._run_teensy_toggle("Stability controller", "setStabilityEnabled", current_enabled)

    @Slot(bool, result=bool)
    def toggleYaw(self, current_enabled: bool) -> bool:
        return self._run_teensy_toggle("Yaw control", "setYawEnabled", current_enabled)

    @Slot(bool, result=bool)
    def toggleAutoCorrection(self, current_enabled: bool) -> bool:
        return self._run_teensy_toggle("Auto correction", "setAutoCorrectonEnabled", current_enabled)

    @Slot(bool, result=bool)
    def toggleSprayGunLeveling(self, current_enabled: bool) -> bool:
        return self._run_teensy_toggle("Spray gun leveling", "setSprayGunLevelingEnabled", current_enabled)

    @Slot(bool, result=bool)
    def toggleRollerSteering(self, current_enabled: bool) -> bool:
        return self._run_teensy_toggle("Roller steering", "setRollerSteeringEnabled", current_enabled)

    @Slot(bool, result=bool)
    def toggleSwingDamping(self, current_enabled: bool) -> bool:
        return self._run_teensy_toggle("Swing damping", "setSwingDampingEnabled", current_enabled)

    @Slot(bool, result=bool)
    def toggleSprayGunLed(self, current_enabled: bool) -> bool:
        return self._run_teensy_toggle("Spray gun LED", "setSprayGunLED", current_enabled)

    @Slot(bool, result=bool)
    def setLidarPower(self, enabled: bool) -> bool:
        return self._run_action(
            name="Lidar power",
            controller=self._teensy,
            method_name="setLidarPower",
            args=(enabled,),
        )

    @Slot(result=bool)
    def clearErrors(self) -> bool:
        return self._run_action(
            name="Clear error states",
            controller=self._heartbeat_handler,
            method_name="clear_error_state",
        )

    def _run_teensy_toggle(self, name: str, method_name: str, current_enabled: bool) -> bool:
        return self._run_toggle(
            name=name,
            controller=self._teensy,
            method_name=method_name,
            next_enabled=not current_enabled,
        )

    def _run_toggle(
        self,
        *,
        name: str,
        controller: Any,
        method_name: str,
        next_enabled: bool,
    ) -> bool:
        return self._run_action(
            name=name,
            controller=controller,
            method_name=method_name,
            args=(next_enabled,),
        )

    def _run_action(
        self,
        *,
        name: str,
        controller: Any,
        method_name: str,
        args: tuple[Any, ...] = (),
    ) -> bool:
        if controller is None:
            return self._fail(f"{name} is unavailable")

        method = getattr(controller, method_name, None)
        if not callable(method):
            return self._fail(f"{name} is unavailable")

        try:
            result = method(*args)
        except Exception as exc:  # pragma: no cover - defensive boundary guard
            return self._fail(f"{name} failed: {exc}")

        if result is False:
            return self._fail(f"{name} was rejected by the backend")

        message = f"{name} requested"
        self._logger.info(message)
        self.operation_result.emit(True, message)
        return True

    def _fail(self, message: str) -> bool:
        self._logger.warning(message)
        self.operation_result.emit(False, message)
        return False