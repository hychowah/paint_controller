"""Python-owned, feature-root action boundary for Teensy toggles and power."""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot


class SupportsTeensyActions(Protocol):
    """Teensy surface used by feature-root actions (not full controller API)."""

    def setRelayEnabled(self, enabled: bool) -> object: ...

    def setEnabled(self, enabled: bool) -> object: ...

    def homeTopRail(self, home: bool) -> object: ...

    def homeArm(self, home: bool) -> object: ...

    def setStabilityEnabled(self, enabled: bool) -> object: ...

    def setYawEnabled(self, enabled: bool) -> object: ...

    def setAutoCorrectionEnabled(self, enabled: bool) -> object: ...

    def setSprayGunLevelingEnabled(self, enabled: bool) -> object: ...

    def setRollerSteeringEnabled(self, enabled: bool) -> object: ...

    def setSwingDampingEnabled(self, enabled: bool) -> object: ...

    def setSprayGunLED(self, on: bool) -> object: ...

    def setLidarPower(self, on: bool) -> object: ...

    def get_status(self) -> dict: ...

    # Intent members (user-controlled flags)
    stability_enabled: bool
    auto_correction_enabled: bool
    spray_gun_leveling_enabled: bool
    roller_steering_enabled: bool
    swing_damping_enabled: bool
    spray_gun_led_on: bool
    _lidar_power: bool


class TeensyActions(QObject):
    """Own Teensy feature toggles and power/home actions initiated from QML.

    Feature toggles stay ungated; power enable/relay use AdminActionGate.
    Home rails stay ungated for field parity.
    TD-055.7: typed invoke — no string method-name dispatch.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: SupportsTeensyActions | None,
        logger: Any,
        admin_action_gate: Any = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._logger = logger
        self._admin_action_gate = admin_action_gate

    @Slot(bool, result=bool)
    def requestTeensyRelayEnabled(self, enabled: bool) -> bool:
        return self._run(
            action_key="status.teensy_relay",
            name="Teensy relay",
            invoke=lambda t: t.setRelayEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleTeensyRelay(self) -> bool:
        return self.requestTeensyRelayEnabled(not self._status_flag("relay_on"))

    @Slot(bool, result=bool)
    def requestTeensyEnabled(self, enabled: bool) -> bool:
        return self._run(
            action_key="status.teensy_enable",
            name="Teensy enable",
            invoke=lambda t: t.setEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleTeensyEnable(self) -> bool:
        return self.requestTeensyEnabled(not self._status_flag("enabled"))

    @Slot(result=bool)
    def homeTopRail(self) -> bool:
        return self._run(name="Home top rail", invoke=lambda t: t.homeTopRail(True))

    @Slot(result=bool)
    def homeArm(self) -> bool:
        return self._run(name="Home arm rail", invoke=lambda t: t.homeArm(True))

    @Slot(result=bool)
    def toggleStability(self) -> bool:
        nxt = not self._intent("stability_enabled")
        return self._run(name="Stability controller", invoke=lambda t: t.setStabilityEnabled(nxt))

    @Slot(result=bool)
    def toggleYaw(self) -> bool:
        nxt = not self._status_flag("yaw_enabled")
        return self._run(name="Yaw control", invoke=lambda t: t.setYawEnabled(nxt))

    @Slot(result=bool)
    def toggleAutoCorrection(self) -> bool:
        nxt = not self._intent("auto_correction_enabled")
        return self._run(name="Auto correction", invoke=lambda t: t.setAutoCorrectionEnabled(nxt))

    @Slot(result=bool)
    def toggleSprayGunLeveling(self) -> bool:
        nxt = not self._intent("spray_gun_leveling_enabled")
        return self._run(name="Spray gun leveling", invoke=lambda t: t.setSprayGunLevelingEnabled(nxt))

    @Slot(result=bool)
    def toggleRollerSteering(self) -> bool:
        nxt = not self._intent("roller_steering_enabled")
        return self._run(name="Roller steering", invoke=lambda t: t.setRollerSteeringEnabled(nxt))

    @Slot(result=bool)
    def toggleSwingDamping(self) -> bool:
        nxt = not self._intent("swing_damping_enabled")
        return self._run(name="Swing damping", invoke=lambda t: t.setSwingDampingEnabled(nxt))

    @Slot(result=bool)
    def toggleSprayGunLed(self) -> bool:
        nxt = not self._intent("spray_gun_led_on")
        return self._run(name="Spray gun LED", invoke=lambda t: t.setSprayGunLED(nxt))

    @Slot(bool, result=bool)
    def setLidarPower(self, enabled: bool) -> bool:
        return self._run(name="Lidar power", invoke=lambda t: t.setLidarPower(enabled))

    @Slot(result=bool)
    def toggleLidarPower(self) -> bool:
        nxt = not self._intent("_lidar_power")
        return self._run(name="Lidar power", invoke=lambda t: t.setLidarPower(nxt))

    def _intent(self, attribute: str) -> bool:
        if self._teensy is None:
            return False
        return bool(getattr(self._teensy, attribute, False))

    def _status_flag(self, key: str) -> bool:
        if self._teensy is None:
            return False
        return bool(self._teensy.get_status().get(key, False))

    def _run(self, *, name: str, invoke, action_key: str | None = None) -> bool:
        if action_key is not None:
            if self._admin_action_gate is None:
                return self._fail(f"{name} gate is unavailable")
            allowed, reason = self._admin_action_gate.check_action(action_key)
            if not allowed:
                return self._fail(reason)

        if self._teensy is None:
            return self._fail(f"{name} is unavailable")

        try:
            result = invoke(self._teensy)
        except Exception as exc:  # pragma: no cover
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
