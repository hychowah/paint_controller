"""Python-owned, feature-root action boundary for Teensy toggles."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class TeensyActions(QObject):
    """Own Teensy feature toggles initiated from QML.

    This model absorbs the Teensy toggle policy previously held by
    ``DeviceOperationsHandler`` so that QML accesses stability, yaw, leveling,
    and LED/lidar controls through a single feature-root object rather than a
    handler-shaped global.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._logger = logger

    @Slot(result=bool)
    def toggleStability(self) -> bool:
        return self._run_toggle("Stability controller", "setStabilityEnabled", not self._teensy_intent("stability_enabled"))

    @Slot(result=bool)
    def toggleYaw(self) -> bool:
        return self._run_toggle("Yaw control", "setYawEnabled", not self._teensy_status_flag("yaw_enabled"))

    @Slot(result=bool)
    def toggleAutoCorrection(self) -> bool:
        return self._run_toggle("Auto correction", "setAutoCorrectonEnabled", not self._teensy_intent("auto_correction_enabled"))

    @Slot(result=bool)
    def toggleSprayGunLeveling(self) -> bool:
        return self._run_toggle("Spray gun leveling", "setSprayGunLevelingEnabled", not self._teensy_intent("spray_gun_leveling_enabled"))

    @Slot(result=bool)
    def toggleRollerSteering(self) -> bool:
        return self._run_toggle("Roller steering", "setRollerSteeringEnabled", not self._teensy_intent("roller_steering_enabled"))

    @Slot(result=bool)
    def toggleSwingDamping(self) -> bool:
        return self._run_toggle("Swing damping", "setSwingDampingEnabled", not self._teensy_intent("swing_damping_enabled"))

    @Slot(result=bool)
    def toggleSprayGunLed(self) -> bool:
        return self._run_toggle("Spray gun LED", "setSprayGunLED", not self._teensy_intent("spray_gun_led_on"))

    @Slot(bool, result=bool)
    def setLidarPower(self, enabled: bool) -> bool:
        return self._run_action(
            name="Lidar power",
            controller=self._teensy,
            method_name="setLidarPower",
            args=(enabled,),
        )

    def _teensy_intent(self, attribute: str) -> bool:
        """Read a controller intent member (False when the controller is missing)."""
        if self._teensy is None:
            return False
        return bool(getattr(self._teensy, attribute, False))

    def _teensy_status_flag(self, key: str) -> bool:
        """Read a firmware-echoed status flag (False when the controller is missing)."""
        if self._teensy is None:
            return False
        return bool(self._teensy.get_status().get(key, False))

    def _run_toggle(
        self,
        name: str,
        method_name: str,
        next_enabled: bool,
    ) -> bool:
        return self._run_action(
            name=name,
            controller=self._teensy,
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
