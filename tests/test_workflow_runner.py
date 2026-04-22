"""Direct tests for the QML-facing workflow runner facade."""

from __future__ import annotations

import importlib
from pathlib import Path

from paint_controller.services.workflow.workflow_executor import ExecutionState
from tests.fakes import FakeNode


class FakeExecutor:
    def __init__(self, _ros_node, _hardware, _logger) -> None:
        self.current_state = ExecutionState.IDLE
        self.current_workflow = None
        self.loaded_paths: list[str] = []
        self._loop_enabled = True
        self._loop_iteration = 4
        self.cleaned_up = False

    def load_workflow(self, workflow_path: str) -> bool:
        self.loaded_paths.append(workflow_path)
        self.current_workflow = {"actions": []}
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
    monkeypatch.setattr(module.WorkFlowRunner, "_find_workflows_dir", lambda self: str(workflows_dir))
    return module.WorkFlowRunner(FakeNode(), hardware=object())


def test_workflow_runner_lists_yaml_workflows_from_directory(qt_app, monkeypatch, tmp_path) -> None:
    (tmp_path / "alpha.yaml").write_text("name: alpha\nactions: []\n")
    (tmp_path / "beta.yml").write_text("name: beta\nactions: []\n")
    (tmp_path / "ignore.txt").write_text("not a workflow\n")

    runner = _make_runner(monkeypatch, tmp_path)
    try:
        assert set(runner.workflow_list) == {"alpha", "beta"}
    finally:
        runner.cleanup()


def test_workflow_runner_load_workflow_updates_public_state(qt_app, monkeypatch, tmp_path) -> None:
    (tmp_path / "demo.yaml").write_text("name: demo\nactions: []\n")
    runner = _make_runner(monkeypatch, tmp_path)

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