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
        admin_action_gate: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._winch = winch
        self._admin_action_gate = admin_action_gate
        self._logger = logger

    @Slot(bool, result=bool)
    def toggleTeensyRelay(self, current_enabled: bool) -> bool:
        return self.requestTeensyRelayEnabled(not current_enabled)

    @Slot(bool, result=bool)
    def toggleTeensyEnable(self, current_enabled: bool) -> bool:
        return self.requestTeensyEnabled(not current_enabled)

    @Slot(bool, result=bool)
    def toggleWinchEnable(self, current_enabled: bool) -> bool:
        return self.requestWinchEnabled(not current_enabled)

    @Slot(bool, result=bool)
    def requestTeensyRelayEnabled(self, enabled: bool) -> bool:
        return self._run_action(
            action_key="status.teensy_relay",
            name="Teensy relay",
            controller=self._teensy,
            method_name="setRelayEnabled",
            args=(enabled,),
        )

    @Slot(bool, result=bool)
    def requestTeensyEnabled(self, enabled: bool) -> bool:
        return self._run_action(
            action_key="status.teensy_enable",
            name="Teensy enable",
            controller=self._teensy,
            method_name="setEnabled",
            args=(enabled,),
        )

    @Slot(bool, result=bool)
    def requestWinchEnabled(self, enabled: bool) -> bool:
        return self._run_action(
            action_key="status.winch_enable",
            name="Winch enable",
            controller=self._winch,
            method_name="setEnabled",
            args=(enabled,),
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
        action_key: str | None = None,
        name: str,
        controller: Any,
        method_name: str,
        args: tuple[Any, ...] = (),
    ) -> bool:
        if action_key is not None:
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