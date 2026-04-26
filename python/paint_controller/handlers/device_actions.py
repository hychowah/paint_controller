"""Python-owned hard device-action boundary for the system-control overlay."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class DeviceActionHandler(QObject):
    """Own high-risk one-click device actions initiated from QML."""

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: Any,
        winch: Any,
        wheel: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._winch = winch
        self._wheel = wheel
        self._logger = logger

    @Slot(bool, result=bool)
    def toggleTeensyRelay(self, current_enabled: bool) -> bool:
        return self._run_toggle(
            name="Teensy relay",
            controller=self._teensy,
            method_name="setRelayEnabled",
            next_enabled=not current_enabled,
        )

    @Slot(bool, result=bool)
    def toggleTeensyEnable(self, current_enabled: bool) -> bool:
        return self._run_toggle(
            name="Teensy enable",
            controller=self._teensy,
            method_name="setEnabled",
            next_enabled=not current_enabled,
        )

    @Slot(bool, result=bool)
    def toggleWinchEnable(self, current_enabled: bool) -> bool:
        return self._run_toggle(
            name="Winch enable",
            controller=self._winch,
            method_name="setEnabled",
            next_enabled=not current_enabled,
        )

    @Slot(bool, result=bool)
    def toggleWheelEnable(self, current_enabled: bool) -> bool:
        return self._run_toggle(
            name="Wheel enable",
            controller=self._wheel,
            method_name="setEnabled",
            next_enabled=not current_enabled,
        )

    @Slot(result=bool)
    def resetWheelPosition(self) -> bool:
        return self._run_action(
            name="Reset wheel position",
            controller=self._wheel,
            method_name="resetWheelPosition",
        )

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