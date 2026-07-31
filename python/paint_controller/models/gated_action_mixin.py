"""Shared helpers for ``*Actions`` classes that gate operator commands.

Keeps the gate check, controller-availability check, exception guard, backend
rejection handling, and ``operation_result`` emission in one place while
leaving the action key and controller surface explicit at each call site.
"""

from __future__ import annotations

from typing import Any

from paint_controller.models.action_keys import ActionKey


class GatedActionMixin:
    """Provide ``_run_gated`` / ``_run_ungated`` and ``_fail`` to ``*Actions``.

    The subclass must supply:
    - ``self._admin_action_gate`` (or ``None`` for ungated-only classes)
    - ``self._logger``
    - ``self.operation_result`` (a Qt ``Signal``)
    """

    _admin_action_gate: Any
    _logger: Any
    operation_result: Any

    def _run_gated(self, *, action_key: ActionKey, name: str, controller: Any, invoke) -> bool:
        if self._admin_action_gate is None:
            return self._fail(f"{name} gate is unavailable")
        allowed, reason = self._admin_action_gate.check_action(action_key)
        if not allowed:
            return self._fail(reason)
        return self._run_ungated(name=name, controller=controller, invoke=invoke)

    def _run_ungated(self, *, name: str, controller: Any, invoke) -> bool:
        if controller is None:
            return self._fail(f"{name} is unavailable")

        try:
            result = invoke(controller)
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
