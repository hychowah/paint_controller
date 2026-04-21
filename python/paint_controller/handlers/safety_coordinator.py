"""Shared halt-all safety path for emergency and comms-loss conditions."""

from __future__ import annotations

from typing import Any

from paint_controller.utils.constants import HeartbeatStatus


class SafetyCoordinator:
    """Coordinates halt-all behavior across safety-trigger paths."""

    def __init__(
        self,
        *,
        winch: Any = None,
        teensy: Any = None,
        wheel: Any = None,
        esp32_valve: Any = None,
        state_store: Any = None,
        logger: Any = None,
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
                if hasattr(self._wheel, 'emergency_stop'):
                    self._wheel.emergency_stop()
                elif hasattr(self._wheel, 'setSpeed'):
                    self._wheel.setSpeed(0, 0)
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
                    'Safety halt for %s completed with %d failure(s): %s',
                    reason,
                    len(failures),
                    '; '.join(failures),
                )
            else:
                self._logger.warning('Safety halt executed: %s', reason)