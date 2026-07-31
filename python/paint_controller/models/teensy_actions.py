"""Python-owned, feature-root action boundary for Teensy toggles and power."""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.models.action_keys import ActionKey
from paint_controller.models.gated_action_mixin import GatedActionMixin


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


class TeensyActions(QObject, GatedActionMixin):
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
        return self._run_gated(
            action_key=ActionKey.STATUS_TEENSY_RELAY,
            name="Teensy relay",
            controller=self._teensy,
            invoke=lambda t: t.setRelayEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleTeensyRelay(self) -> bool:
        return self.requestTeensyRelayEnabled(not self._status_flag("relay_on"))

    @Slot(bool, result=bool)
    def requestTeensyEnabled(self, enabled: bool) -> bool:
        return self._run_gated(
            action_key=ActionKey.STATUS_TEENSY_ENABLE,
            name="Teensy enable",
            controller=self._teensy,
            invoke=lambda t: t.setEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleTeensyEnable(self) -> bool:
        return self.requestTeensyEnabled(not self._status_flag("enabled"))

    @Slot(result=bool)
    def homeTopRail(self) -> bool:
        return self._run_ungated(name="Home top rail", controller=self._teensy, invoke=lambda t: t.homeTopRail(True))

    @Slot(result=bool)
    def homeArm(self) -> bool:
        return self._run_ungated(name="Home arm rail", controller=self._teensy, invoke=lambda t: t.homeArm(True))

    @Slot(result=bool)
    def toggleStability(self) -> bool:
        nxt = not self._intent("stability_enabled")
        return self._run_ungated(name="Stability controller", controller=self._teensy, invoke=lambda t: t.setStabilityEnabled(nxt))

    @Slot(result=bool)
    def toggleYaw(self) -> bool:
        nxt = not self._status_flag("yaw_enabled")
        return self._run_ungated(name="Yaw control", controller=self._teensy, invoke=lambda t: t.setYawEnabled(nxt))

    @Slot(result=bool)
    def toggleAutoCorrection(self) -> bool:
        nxt = not self._intent("auto_correction_enabled")
        return self._run_ungated(name="Auto correction", controller=self._teensy, invoke=lambda t: t.setAutoCorrectionEnabled(nxt))

    @Slot(result=bool)
    def toggleSprayGunLeveling(self) -> bool:
        nxt = not self._intent("spray_gun_leveling_enabled")
        return self._run_ungated(name="Spray gun leveling", controller=self._teensy, invoke=lambda t: t.setSprayGunLevelingEnabled(nxt))

    @Slot(result=bool)
    def toggleRollerSteering(self) -> bool:
        nxt = not self._intent("roller_steering_enabled")
        return self._run_ungated(name="Roller steering", controller=self._teensy, invoke=lambda t: t.setRollerSteeringEnabled(nxt))

    @Slot(result=bool)
    def toggleSwingDamping(self) -> bool:
        nxt = not self._intent("swing_damping_enabled")
        return self._run_ungated(name="Swing damping", controller=self._teensy, invoke=lambda t: t.setSwingDampingEnabled(nxt))

    @Slot(result=bool)
    def toggleSprayGunLed(self) -> bool:
        nxt = not self._intent("spray_gun_led_on")
        return self._run_ungated(name="Spray gun LED", controller=self._teensy, invoke=lambda t: t.setSprayGunLED(nxt))

    @Slot(bool, result=bool)
    def setLidarPower(self, enabled: bool) -> bool:
        return self._run_ungated(name="Lidar power", controller=self._teensy, invoke=lambda t: t.setLidarPower(enabled))

    @Slot(result=bool)
    def toggleLidarPower(self) -> bool:
        nxt = not self._intent("_lidar_power")
        return self._run_ungated(name="Lidar power", controller=self._teensy, invoke=lambda t: t.setLidarPower(nxt))

    def _intent(self, attribute: str) -> bool:
        if self._teensy is None:
            return False
        return bool(getattr(self._teensy, attribute, False))

    def _status_flag(self, key: str) -> bool:
        if self._teensy is None:
            return False
        return bool(self._teensy.get_status().get(key, False))
