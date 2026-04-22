"""Direct tests for the workflow executor control-path seams."""

from __future__ import annotations

import importlib

from paint_controller.services.workflow.scheduler import ScheduledAction


class _FakeLogger:
    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.debugs: list[str] = []

    def debug(self, message: str, *args) -> None:
        self.debugs.append(message % args if args else message)

    def info(self, message: str, *args) -> None:
        self.infos.append(message % args if args else message)

    def warn(self, message: str, *args) -> None:
        self.warnings.append(message % args if args else message)

    def warning(self, message: str, *args) -> None:
        self.warn(message, *args)

    def error(self, message: str, *args) -> None:
        self.errors.append(message % args if args else message)


class _FakeNode:
    def __init__(self, logger: _FakeLogger) -> None:
        self._logger = logger

    def get_logger(self) -> _FakeLogger:
        return self._logger


class _FakeSignal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)


class _FakeExecutionThread:
    def __init__(self, executor, scheduled_actions, all_scheduled) -> None:
        self.executor = executor
        self.scheduled_actions = scheduled_actions
        self.all_scheduled = all_scheduled
        self.execution_finished = _FakeSignal()
        self.execution_error = _FakeSignal()
        self.started = False
        self.stop_requested = False
        self.wait_calls: list[int] = []

    def start(self) -> None:
        self.started = True

    def request_stop(self) -> None:
        self.stop_requested = True

    def wait(self, timeout: int) -> bool:
        self.wait_calls.append(timeout)
        return True


def _executor_module():
    return importlib.import_module("paint_controller.services.workflow.workflow_executor")


def test_workflow_executor_load_play_and_stop_manage_state(monkeypatch, tmp_path) -> None:
    module = _executor_module()
    monkeypatch.setattr(module, "WorkFlowExecutionThread", _FakeExecutionThread)

    logger = _FakeLogger()
    executor = module.WorkFlowExecutor(_FakeNode(logger), hardware=object(), logger=logger)
    workflow_path = tmp_path / "demo.yaml"
    workflow_path.write_text("name: demo\nloop: true\nactions:\n  - id: move\n    type: winch_increment\n")

    assert executor.load_workflow(str(workflow_path)) is True
    assert executor.is_loop_enabled() is True
    assert executor.get_loop_iteration() == 0

    scheduled = [
        ScheduledAction(
            action_index=0,
            action_id="move",
            action_config={"type": "winch_increment", "params": {"length": 50}},
            scheduled_time=0.0,
            estimated_duration=1.0,
            is_winch_action=True,
            winch_target_mm=50,
        ),
        ScheduledAction(
            action_index=1,
            action_id="spray",
            action_config={"type": "valve_turn", "params": {"turn_value": 25.0}},
            scheduled_time=-1.0,
            estimated_duration=0.0,
            is_position_triggered=True,
            position_trigger_mm=40.0,
            position_reference_action="move",
        ),
    ]
    monkeypatch.setattr(executor.scheduler, "build_schedule", lambda actions: scheduled)

    assert executor.play() is True
    assert executor.current_state == module.ExecutionState.RUNNING
    assert executor.get_loop_iteration() == 1
    assert executor.execution_thread.started is True
    assert [action.action_id for action in executor.execution_thread.scheduled_actions] == ["move"]
    assert [action.action_id for action in executor._pending_position_triggers] == ["spray"]

    assert executor.stop() is True
    assert executor.execution_thread.stop_requested is True
    assert executor.execution_thread.wait_calls == [5000]
    assert executor.current_state == module.ExecutionState.IDLE
    assert executor.current_action_index == -1
    assert executor.get_loop_iteration() == 0


def test_workflow_executor_completion_and_error_callbacks_reset_public_state() -> None:
    module = _executor_module()
    logger = _FakeLogger()
    executor = module.WorkFlowExecutor(_FakeNode(logger), hardware=object(), logger=logger)

    executor.current_state = module.ExecutionState.RUNNING
    executor.current_action_index = 3
    executor._on_execution_finished()

    assert executor.current_state == module.ExecutionState.COMPLETED
    assert executor.current_action_index == -1

    executor.current_state = module.ExecutionState.RUNNING
    executor.current_action_index = 2
    executor._on_execution_error("boom")

    assert executor.current_state == module.ExecutionState.ERROR
    assert executor.current_action_index == -1
    assert logger.errors[-1] == "WorkFlow execution error: boom"