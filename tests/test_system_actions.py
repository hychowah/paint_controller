"""Focused tests for the feature-root system action boundary."""

from __future__ import annotations

from paint_controller.models.system_actions import SystemActions
from tests.fakes import FakeLogger


class FakeHeartbeatHandler:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.clear_calls = 0

    def clear_error_state(self) -> bool:
        self.clear_calls += 1
        return self.result


def _build_actions(
    result: bool = True,
) -> tuple[SystemActions, FakeHeartbeatHandler, FakeLogger, list[tuple[bool, str]]]:
    heartbeat_handler = FakeHeartbeatHandler(result=result)
    logger = FakeLogger()
    actions = SystemActions(
        heartbeat_handler=heartbeat_handler,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))
    return actions, heartbeat_handler, logger, results


def test_clear_errors_dispatches_to_heartbeat_handler() -> None:
    actions, heartbeat, logger, results = _build_actions()

    assert actions.clearErrors() is True

    assert heartbeat.clear_calls == 1
    assert results[-1] == (True, "Clear error states requested")
    assert logger.records[-1].message == "Clear error states requested"


def test_backend_rejection_is_reported() -> None:
    actions, heartbeat, _logger, results = _build_actions(result=False)

    assert actions.clearErrors() is False

    assert heartbeat.clear_calls == 1
    assert results[-1] == (False, "Clear error states was rejected by the backend")


def test_missing_controller_is_reported() -> None:
    logger = FakeLogger()
    actions = SystemActions(
        heartbeat_handler=None,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))

    assert actions.clearErrors() is False

    assert results[-1] == (False, "Clear error states is unavailable")
    assert logger.records[-1].message == "Clear error states is unavailable"
