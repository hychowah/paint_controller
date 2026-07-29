"""Teensy effector Protocols shared by teleop, safety, and workflow (TD-049)."""

from __future__ import annotations

from typing import Any, Protocol


class SupportsTeensyStatusRead(Protocol):
    def get_status_value(self, key: str) -> Any: ...


class SupportsTeensyHalt(Protocol):
    """Neutral spray trigger for safety halt (value 1000)."""

    def setSprayTrigger(self, value: int) -> None: ...


class SupportsTeensyTeleop(SupportsTeensyStatusRead, SupportsTeensyHalt, Protocol):
    """Continuous teleop surface used by ControlProcessor."""

    def setLeftPropJoint(self, position: float) -> None: ...

    def setRightPropJoint(self, position: float) -> None: ...

    def setArmRailSpeed(self, speed: float) -> None: ...

    def setTopRailSpeed(self, speed: float) -> None: ...

    def setLeftPropPWM(self, pwm: int) -> None: ...

    def setRightPropPWM(self, pwm: int) -> None: ...

    def setSprayPitchSpeed(self, speed: int) -> None: ...

    def set_ef_force(self, fx: float, fy: float) -> None: ...

    def setYawAngle(self, angle: float) -> None: ...


class SupportsTeensyWorkflowBody(Protocol):
    """Methods the workflow Teensy adapter needs on the real controller body.

    Names match production ``TeensyController`` (gimbal uses pitch angle API).
    """

    def extendArm(self, dist: int) -> None: ...

    def set_ef_force(self, fx: float, fy: float) -> None: ...

    def setSprayGunPitchAngle(self, angle: float, speed: float) -> None: ...
