"""Shared halt-all safety path for emergency and comms-loss conditions.

TD-054: also owns the continuous-motion latch. After any ``halt_all_effectors``,
stick teleop must not re-command until ``clear_error_state``. Optional
``command_bus.invalidate_continuous`` drops stale teleop publishes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from paint_controller.ports.halt import SupportsValveHalt, SupportsWheelHalt, SupportsWinchHalt
from paint_controller.ports.teensy import SupportsTeensyHalt
from paint_controller.utils.constants import HeartbeatStatus

if TYPE_CHECKING:
    from paint_controller.core.state_store import StateStore


class LoggerProtocol(Protocol):
    def error(self, message: str) -> object: ...

    def warning(self, message: str) -> object: ...


class SafetyCoordinator:
    """Coordinates halt-all behavior and continuous-motion latch (TD-054)."""

    def __init__(
        self,
        *,
        winch: SupportsWinchHalt | None = None,
        teensy: SupportsTeensyHalt | None = None,
        wheel: SupportsWheelHalt | None = None,
        esp32_valve: SupportsValveHalt | None = None,
        state_store: StateStore | None = None,
        logger: LoggerProtocol | None = None,
        command_bus: Any | None = None,
    ) -> None:
        self._winch = winch
        self._teensy = teensy
        self._wheel = wheel
        self._esp32_valve = esp32_valve
        self._state_store = state_store
        self._logger = logger
        self._command_bus = command_bus
        self._execution_stop: Any | None = None
        # Fail-open until first halt; then latched until clear_error_state.
        self._continuous_motion_allowed = True

    @property
    def continuous_motion_allowed(self) -> bool:
        """False after halt until clear_error_state (continuous teleop / thrust / workflow play)."""
        return self._continuous_motion_allowed

    def bind_execution_stop(self, execution_stop: Any | None) -> None:
        """Late-bind workflow runner (or any object with stop_execution())."""
        self._execution_stop = execution_stop

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
        self._continuous_motion_allowed = True
        self._set_runtime_state(HeartbeatStatus.IDLE, force=True)

    def halt_all_effectors(
        self,
        reason: str,
        *,
        heartbeat_state: int | HeartbeatStatus = HeartbeatStatus.ERROR,
    ) -> None:
        # 1) Latch continuous teleop / workflow play
        self._continuous_motion_allowed = False
        # 2) Drop pending continuous teleop publishes
        if self._command_bus is not None:
            try:
                self._command_bus.invalidate_continuous()
            except Exception as exc:
                if self._logger is not None:
                    self._logger.error(f"command bus invalidate failed during halt: {exc}")

        # 3) Non-blocking workflow stop request (before zeros; no join / no runner matrix)
        if self._execution_stop is not None:
            try:
                stop_fn = getattr(self._execution_stop, "stop_execution", None)
                if callable(stop_fn):
                    stop_fn()
            except Exception as exc:
                if self._logger is not None:
                    self._logger.error(f"execution stop failed during halt: {exc}")

        self._set_runtime_state(heartbeat_state)

        # 4) Device halt matrix
        failures: list[str] = []

        try:
            if self._winch is not None:
                self._winch.command_speed_rpm(0)
        except Exception as exc:
            failures.append(f"winch: {exc}")

        try:
            if self._teensy is not None:
                self._teensy.setSprayTrigger(1000)
                suppress = getattr(self._teensy, "suppress_continuous_thrust", None)
                if callable(suppress):
                    suppress()
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
                self._logger.warning(f"Safety halt executed: {reason}")