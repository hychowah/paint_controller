"""Direct tests for the QML-facing workflow runner facade."""

from __future__ import annotations

import importlib
from pathlib import Path

from paint_controller.services.workflow.workflow_catalog import WorkflowCatalog
from paint_controller.services.workflow.workflow_executor import ExecutionState
from tests.fakes import FakeNode


class FakeExecutor:
    def __init__(self, _ros_node, _hardware, _logger) -> None:
        self.current_state = ExecutionState.IDLE
        self.current_workflow = None
        self.current_action_index = -1
        self.loaded_paths: list[str] = []
        self._loop_enabled = True
        self._loop_iteration = 4
        self.cleaned_up = False
        self.play_calls = 0
        self.pause_calls = 0
        self.resume_calls = 0
        self.stop_calls = 0
        self.hardware = type(
            "Hardware",
            (),
            {
                "winch": type("Winch", (), {"move_absolute": lambda self, length, speed: None})(),
                "teensy": type("Teensy", (), {"set_valve_turn": lambda self, value: None})(),
            },
        )()

    def load_workflow(self, workflow_path: str) -> bool:
        self.loaded_paths.append(workflow_path)
        self.current_workflow = {
            "name": "demo",
            "actions": [
                {
                    "id": "move",
                    "name": "Move Winch",
                    "type": "winch_absolute",
                    "params": {"length": 420, "speed": 35},
                },
                {
                    "id": "spray",
                    "name": "Open Valve",
                    "type": "valve_turn",
                    "params": {"turn_value": 25.0},
                    "trigger": {
                        "reference_action": "move",
                        "timing_mode": "before_complete",
                        "offset_ms": 250,
                    },
                },
            ],
        }
        return True

    def play(self) -> bool:
        self.play_calls += 1
        if not self.current_workflow:
            return False
        self.current_state = ExecutionState.RUNNING
        return True

    def pause(self) -> bool:
        self.pause_calls += 1
        if self.current_state != ExecutionState.RUNNING:
            return False
        self.current_state = ExecutionState.PAUSED
        return True

    def resume(self) -> bool:
        self.resume_calls += 1
        if self.current_state != ExecutionState.PAUSED:
            return False
        self.current_state = ExecutionState.RUNNING
        return True

    def stop(self) -> bool:
        self.stop_calls += 1
        if self.current_state == ExecutionState.IDLE:
            return True
        self.current_state = ExecutionState.IDLE
        self.current_action_index = -1
        return True

    def is_loop_enabled(self) -> bool:
        return self._loop_enabled

    def get_loop_iteration(self) -> int:
        return self._loop_iteration

    def cleanup(self) -> None:
        self.cleaned_up = True


def _workflow_runner_module():
    return importlib.import_module("paint_controller.services.workflow.workflow_runner")


def _make_runner(monkeypatch, workflows_dir: Path):
    module = _workflow_runner_module()
    monkeypatch.setattr(module, "WorkFlowExecutor", FakeExecutor)
    logger = FakeNode().get_logger()
    catalog = WorkflowCatalog(workflows_dir=str(workflows_dir), logger=logger)
    runner = module.WorkFlowRunner(FakeNode(), hardware=object(), catalog=catalog)
    return runner, catalog


def test_workflow_runner_lists_yaml_workflows_from_directory(qt_app, monkeypatch, tmp_path) -> None:
    (tmp_path / "alpha.yaml").write_text("name: alpha\nactions: []\n")
    (tmp_path / "beta.yml").write_text("name: beta\nactions: []\n")
    (tmp_path / "ignore.txt").write_text("not a workflow\n")

    runner, catalog = _make_runner(monkeypatch, tmp_path)
    try:
        assert set(runner.workflow_list) == {"alpha", "beta"}
    finally:
        runner.cleanup()
        catalog.cleanup()


def test_workflow_runner_load_workflow_updates_public_state(qt_app, monkeypatch, tmp_path) -> None:
    (tmp_path / "demo.yaml").write_text("name: demo\nactions: []\n")
    runner, catalog = _make_runner(monkeypatch, tmp_path)

    current_names: list[str] = []
    loop_enabled_events: list[bool] = []
    loop_iterations: list[int] = []
    runner.current_workflow_changed.connect(current_names.append)
    runner.loop_enabled_changed.connect(loop_enabled_events.append)
    runner.loop_iteration_changed.connect(loop_iterations.append)

    try:
        assert runner.load_workflow("demo") is True
        assert runner.current_workflow == "demo"
        assert runner.executor.loaded_paths == [str(tmp_path / "demo.yaml")]
        assert current_names == ["demo"]
        assert loop_enabled_events == [True]
        assert loop_iterations == [0]
    finally:
        runner.cleanup()
        catalog.cleanup()


def test_workflow_runner_rejects_loading_new_workflow_while_active(qt_app, monkeypatch, tmp_path) -> None:
    (tmp_path / "alpha.yaml").write_text("name: alpha\nactions: []\n", encoding="utf-8")
    (tmp_path / "beta.yaml").write_text("name: beta\nactions: []\n", encoding="utf-8")
    runner, catalog = _make_runner(monkeypatch, tmp_path)
    errors: list[str] = []
    runner.error_occurred.connect(errors.append)

    try:
        assert runner.load_workflow("alpha") is True
        assert runner.play() is True
        assert runner.load_workflow("beta") is False
        assert runner.current_workflow == "alpha"
        assert runner.executor.loaded_paths == [str(tmp_path / "alpha.yaml")]
        assert errors[-1] == "Cannot load a new workflow while execution is active; stop the current workflow first"
    finally:
        runner.cleanup()
        catalog.cleanup()


def test_workflow_runner_controls_execution_and_stop_hardware_matrix(qt_app, monkeypatch, tmp_path) -> None:
    (tmp_path / "demo.yaml").write_text("name: demo\nactions: []\n", encoding="utf-8")
    runner, catalog = _make_runner(monkeypatch, tmp_path)
    state_events: list[int] = []
    errors: list[str] = []
    winch_calls: list[tuple[int, int]] = []
    valve_calls: list[float] = []
    runner.execution_state_changed.connect(state_events.append)
    runner.error_occurred.connect(errors.append)
    runner.executor.hardware.winch.move_absolute_with_accel = (
        lambda length, speed, acceleration=30: winch_calls.append((length, speed))
    )
    runner.executor.hardware.teensy.setValveTurn = lambda value: valve_calls.append(value)

    try:
        assert runner.load_workflow("demo") is True
        assert runner.play() is True
        assert runner.pause() is True
        assert runner.resume() is True
        assert runner.stop() is True
        # Second stop while Idle: success, no ERROR, no second hardware matrix.
        assert runner.stop() is True

        assert state_events == [
            ExecutionState.RUNNING.value,
            ExecutionState.PAUSED.value,
            ExecutionState.RUNNING.value,
            ExecutionState.IDLE.value,
        ]
        assert runner.executor.play_calls == 1
        assert runner.executor.pause_calls == 1
        assert runner.executor.resume_calls == 1
        # Runner short-circuits before executor when already Idle.
        assert runner.executor.stop_calls == 1
        assert winch_calls == [(0, 1)]
        assert valve_calls == [0.0]
        assert errors == []
    finally:
        runner.cleanup()
        catalog.cleanup()


def test_workflow_runner_exposes_cached_action_read_model(qt_app, monkeypatch, tmp_path) -> None:
    (tmp_path / "demo.yaml").write_text("name: demo\nactions: []\n", encoding="utf-8")
    runner, catalog = _make_runner(monkeypatch, tmp_path)

    try:
        assert runner.load_workflow("demo") is True
        assert runner.workflow_action_count == 2
        assert runner.workflow_actions[0]["display_name"] == "1. Move Winch"
        assert "Move to 420mm at 35mm/s" in runner.workflow_actions[0]["description"]

        runner.executor.current_action_index = 1
        runner._update_execution_state()

        assert runner.current_action_name == "Open Valve"
        assert runner.current_action_display == "2. Open Valve"
        assert runner.current_action_description == "Open valve to 25.0 (250ms before 'move' completes)"
        assert runner.workflow_progress_text == "2 / 2"
        assert runner.get_current_workflow_actions() == runner.workflow_actions
    finally:
        runner.cleanup()
        catalog.cleanup()


def test_workflow_runner_runtime_document_collision_rules(qt_app, monkeypatch, tmp_path) -> None:
    (tmp_path / "demo.yaml").write_text("name: demo\nactions: []\n", encoding="utf-8")
    runner, catalog = _make_runner(monkeypatch, tmp_path)

    try:
        assert runner.load_workflow("demo") is True

        allowed, error_msg = runner.can_save_workflow_document("demo")
        assert allowed is True
        assert error_msg is None

        runner.mark_workflow_document_saved("demo")
        assert runner.loaded_workflow_needs_reload is True

        runner.executor.current_state = ExecutionState.RUNNING
        allowed, error_msg = runner.can_save_workflow_document("demo")
        assert allowed is False
        assert error_msg == (
            "Cannot save workflow 'demo' while it is running or paused; stop it or load a different workflow first"
        )

        delete_allowed, delete_error = runner.can_delete_workflow_document("demo")
        assert delete_allowed is False
        assert delete_error == "Cannot delete workflow 'demo' while it is loaded; load a different workflow first"

        assert runner.load_workflow("demo") is False
        runner.executor.current_state = ExecutionState.IDLE
        assert runner.load_workflow("demo") is True
        assert runner.loaded_workflow_needs_reload is False
    finally:
        runner.cleanup()
        catalog.cleanup()
