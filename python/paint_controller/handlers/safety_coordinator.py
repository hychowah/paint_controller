"""Shared halt-all safety path for emergency and comms-loss conditions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from paint_controller.utils.constants import HeartbeatStatus

if TYPE_CHECKING:
    from paint_controller.controllers.esp32_valve import ESP32ValveController
    from paint_controller.controllers.teensy import TeensyController
    from paint_controller.controllers.wheel import WheelController
    from paint_controller.controllers.winch import WinchController
    from paint_controller.core.state_store import StateStore


class LoggerProtocol(Protocol):
    def error(self, message: str) -> object: ...

    def warning(self, message: str) -> object: ...


class SafetyCoordinator:
    """Coordinates halt-all behavior across safety-trigger paths."""

    def __init__(
        self,
        *,
        winch: WinchController | None = None,
        teensy: TeensyController | None = None,
        wheel: WheelController | None = None,
        esp32_valve: ESP32ValveController | None = None,
        state_store: StateStore | None = None,
        logger: LoggerProtocol | None = None,
    ) -> None:
        self._winch = winch
        self._teensy = teensy
        self._wheel = wheel
        self._esp32_valve = esp32_valve
        self._state_store = state_store
        self._logger = logger

    def _set_runtime_state(self, heartbeat_state: int | HeartbeatStatus, *, force: bool = False) -> None:
        if self._state_store is None:
            return

        new_state = HeartbeatStatus(heartbeat_state)
        try:
            current_state = HeartbeatStatus(self._state_store.controller_heartbeat_state)
        except (TypeError, ValueError):
            current_state = HeartbeatStatus.IDLE

        if current_state == HeartbeatStatus.ERROR and new_state != HeartbeatStatus.ERROR and not force:
            return

        self._state_store.controller_heartbeat_state = int(new_state)

    def clear_error_state(self) -> None:
        self._set_runtime_state(HeartbeatStatus.IDLE, force=True)

    def halt_all_effectors(
        self,
        reason: str,
        *,
        heartbeat_state: int | HeartbeatStatus = HeartbeatStatus.ERROR,
    ) -> None:
        self._set_runtime_state(heartbeat_state)

        failures: list[str] = []

        try:
            if self._winch is not None:
                self._winch.command_speed_rpm(0)
        except Exception as exc:
            failures.append(f"winch: {exc}")

        try:
            if self._teensy is not None:
                self._teensy.setSprayTrigger(1000)
        except Exception as exc:
            failures.append(f"teensy: {exc}")

        try:
            if self._wheel is not None:
                self._wheel.emergency_stop()
        except Exception as exc:
            failures.append(f"wheel: {exc}")

        try:
            if self._esp32_valve is not None:
                self._esp32_valve.setValveTurn(0.0)
        except Exception as exc:
            failures.append(f"esp32_valve: {exc}")

        if self._logger is not None:
            if failures:
                self._logger.error(
                    f"Safety halt for {reason} completed with {len(failures)} failure(s): {'; '.join(failures)}"
                )
            else:
                self._logger.warning(f'Safety halt executed: {reason}')