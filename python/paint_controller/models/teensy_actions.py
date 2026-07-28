"""Python-owned, feature-root action boundary for Teensy toggles and power."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class TeensyActions(QObject):
    """Own Teensy feature toggles and power/home actions initiated from QML.

    Feature toggles (stability, yaw, LED, …) stay ungated as today.
    Power enable/relay use AdminActionGate (TD-032, absorbed from DeviceActionHandler).
    Home rails stay ungated for field parity with the former handler.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: Any,
        logger: Any,
        admin_action_gate: Any = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._logger = logger
        self._admin_action_gate = admin_action_gate

    # --- Power / enable (gated) ---

    @Slot(bool, result=bool)
    def requestTeensyRelayEnabled(self, enabled: bool) -> bool:
        return self._run_action(
            action_key="status.teensy_relay",
            name="Teensy relay",
            controller=self._teensy,
            method_name="setRelayEnabled",
            args=(enabled,),
        )

    @Slot(result=bool)
    def toggleTeensyRelay(self) -> bool:
        return self.requestTeensyRelayEnabled(not self._teensy_status_flag("relay_on"))

    @Slot(bool, result=bool)
    def requestTeensyEnabled(self, enabled: bool) -> bool:
        return self._run_action(
            action_key="status.teensy_enable",
            name="Teensy enable",
            controller=self._teensy,
            method_name="setEnabled",
            args=(enabled,),
        )

    @Slot(result=bool)
    def toggleTeensyEnable(self) -> bool:
        return self.requestTeensyEnabled(not self._teensy_status_flag("enabled"))

    # --- Home rails (ungated; field parity with DeviceActionHandler) ---

    @Slot(result=bool)
    def homeTopRail(self) -> bool:
        return self._run_action(
            name="Home top rail",
            controller=self._teensy,
            method_name="homeTopRail",
            args=(True,),
        )

    @Slot(result=bool)
    def homeArm(self) -> bool:
        return self._run_action(
            name="Home arm rail",
            controller=self._teensy,
            method_name="homeArm",
            args=(True,),
        )

    # --- Feature toggles (ungated) ---

    @Slot(result=bool)
    def toggleStability(self) -> bool:
        return self._run_toggle("Stability controller", "setStabilityEnabled", not self._teensy_intent("stability_enabled"))

    @Slot(result=bool)
    def toggleYaw(self) -> bool:
        return self._run_toggle("Yaw control", "setYawEnabled", not self._teensy_status_flag("yaw_enabled"))

    @Slot(result=bool)
    def toggleAutoCorrection(self) -> bool:
        return self._run_toggle("Auto correction", "setAutoCorrectionEnabled", not self._teensy_intent("auto_correction_enabled"))

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

    @Slot(result=bool)
    def toggleLidarPower(self) -> bool:
        return self._run_toggle("Lidar power", "setLidarPower", not self._teensy_intent("_lidar_power"))

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
        action_key: str | None = None,
    ) -> bool:
        if action_key is not None:
            if self._admin_action_gate is None:
                return self._fail(f"{name} gate is unavailable")
            allowed, reason = self._admin_action_gate.check_action(action_key)
            if not allowed:
                return self._fail(reason)

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
