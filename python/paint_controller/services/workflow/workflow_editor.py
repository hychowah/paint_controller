"""QML-facing workflow editor persistence boundary."""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING, Any

import yaml
from PySide6.QtCore import Property, QObject, Signal, Slot

from .action_schema import validate_action_params
from .workflow_catalog import WorkflowCatalog

if TYPE_CHECKING:
    from .workflow_runner import WorkFlowRunner


class WorkflowEditor(QObject):
    """Own workflow file read/write/delete operations for the editor surface."""

    workflow_list_changed = Signal()
    error_occurred = Signal(str)

    def __init__(self, catalog: WorkflowCatalog, logger, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._logger = logger
        self._runner: WorkFlowRunner | None = None
        self._catalog.workflow_list_changed.connect(self.workflow_list_changed.emit)

    def attach_runtime(self, runner: WorkFlowRunner) -> None:
        """Attach the runtime owner so editor mutations follow runtime collision rules."""
        self._runner = runner

    @Property(list, notify=workflow_list_changed)
    def workflow_list(self) -> list[str]:
        names = self._catalog.workflow_list
        return list(names) if not callable(names) else list(names())

    @Slot()
    def refresh_workflow_list(self) -> None:
        self._catalog.refresh_workflow_list()

    @Slot(str, result="QVariant")
    def load_document(self, workflow_name: str) -> dict[str, Any]:
        """Load a workflow file into a QML-friendly document map.

        Returns ``{}`` on failure and emits :pyattr:`error_occurred`.
        Success documents always include ``name``, ``description``, ``loop``, and ``actions``.
        """
        if not self._catalog.contains(workflow_name):
            error_msg = f"WorkFlow not found: {workflow_name}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return {}

        workflow_path = self._catalog.resolve_workflow_path(workflow_name)
        if workflow_path is None:
            error_msg = f"WorkFlow file not found: {workflow_name}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return {}

        try:
            with open(workflow_path, encoding="utf-8") as handle:
                workflow_data = yaml.safe_load(handle)
            return self._document_for_edit(workflow_name, workflow_data)
        except Exception as exc:
            error_msg = f"Error loading workflow data: {exc}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return {}

    @Slot(str, str, bool, list, result=bool)
    def save_document(
        self,
        workflow_name: str,
        description: str,
        loop: bool,
        actions: list,
    ) -> bool:
        """Assemble the workflow document in Python and persist it."""
        workflow_data = {
            "name": workflow_name,
            "description": description,
            "loop": bool(loop),
            "actions": list(actions) if actions is not None else [],
        }
        return self._persist_workflow(workflow_name, workflow_data)

    @Slot(str, result=bool)
    def delete_workflow(self, workflow_name: str) -> bool:
        if not self._catalog.contains(workflow_name):
            error_msg = f"WorkFlow not found: {workflow_name}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        if self._runner is not None:
            allowed, error_msg = self._runner.can_delete_workflow_document(workflow_name)
            if not allowed:
                assert error_msg is not None
                self._logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False

        workflow_path = self._catalog.resolve_workflow_path(workflow_name)
        if workflow_path is None:
            error_msg = f"WorkFlow file not found: {workflow_name}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        try:
            os.remove(workflow_path)
            self._logger.info(f"Deleted workflow: {workflow_path}")
            self._catalog.refresh_workflow_list()
            return True
        except Exception as exc:
            error_msg = f"Error deleting workflow: {exc}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def _document_for_edit(self, workflow_name: str, workflow_data: Any) -> dict[str, Any]:
        """Shape a loaded YAML document for the editor UI without full save normalization."""
        if workflow_data is None:
            workflow_data = {}
        if not isinstance(workflow_data, dict):
            raise ValueError("Workflow document must be a mapping")

        actions = workflow_data.get("actions", [])
        if actions is None:
            actions = []
        if not isinstance(actions, list):
            raise ValueError("Workflow actions must be a list")

        return {
            "name": str(workflow_data.get("name") or workflow_name),
            "description": str(workflow_data.get("description", "")),
            "loop": bool(workflow_data.get("loop", False)),
            "actions": actions,
        }

    def _persist_workflow(self, workflow_name: str, workflow_data: dict[str, Any]) -> bool:
        """Shared save path: collision → normalize → atomic write → catalog/runtime notify."""
        try:
            if self._runner is not None:
                allowed, error_msg = self._runner.can_save_workflow_document(workflow_name)
                if not allowed:
                    assert error_msg is not None
                    self._logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    return False

            # Coerce nested Qt/JS maps into plain Python dicts before normalize.
            plain_data = self._coerce_plain_document(workflow_data)
            normalized_workflow = self._normalize_workflow_data(workflow_name, plain_data)

            existing_path = self._catalog.resolve_workflow_path(workflow_name)
            if existing_path is not None:
                workflow_path = existing_path
            else:
                workflow_path = os.path.join(self._catalog.workflows_dir, f"{workflow_name}.yaml")

            self._write_workflow_file_atomic(workflow_path, normalized_workflow)

            self._logger.info(f"Saved workflow: {workflow_path}")
            self._catalog.refresh_workflow_list()
            if self._runner is not None:
                self._runner.mark_workflow_document_saved(workflow_name)
            return True
        except Exception as exc:
            error_msg = f"Error saving workflow: {exc}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def _coerce_plain_document(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Convert QVariantMap / nested containers into plain Python structures."""
        return {
            "name": workflow_data.get("name"),
            "description": workflow_data.get("description", ""),
            "loop": workflow_data.get("loop", False),
            "actions": [self._coerce_plain_action(action) for action in list(workflow_data.get("actions") or [])],
        }

    def _coerce_plain_action(self, action: Any) -> Any:
        if action is None:
            return action
        if not isinstance(action, dict):
            # QVariantMap often presents as a mapping-like object; try dict().
            try:
                action = dict(action)
            except Exception:
                return action

        plain = dict(action)
        params = plain.get("params", {})
        if params is not None and not isinstance(params, dict):
            try:
                params = dict(params)
            except Exception:
                pass
        if isinstance(params, dict):
            plain["params"] = dict(params)

        trigger = plain.get("trigger")
        if trigger is not None and not isinstance(trigger, dict):
            try:
                trigger = dict(trigger)
            except Exception:
                pass
        if isinstance(trigger, dict):
            plain["trigger"] = dict(trigger)

        return plain

    def _normalize_workflow_data(self, workflow_name: str, workflow_data: Any) -> dict[str, Any]:
        if not isinstance(workflow_data, dict):
            raise ValueError("Workflow document must be a JSON object")

        normalized = dict(workflow_data)
        normalized["name"] = workflow_name
        normalized["description"] = str(normalized.get("description", ""))
        normalized["loop"] = bool(normalized.get("loop", False))

        actions = normalized.get("actions", [])
        if not isinstance(actions, list):
            raise ValueError("Workflow actions must be a list")

        normalized["actions"] = [self._normalize_action_data(action, index) for index, action in enumerate(actions)]
        return normalized

    def _normalize_action_data(self, action: Any, index: int) -> dict[str, Any]:
        if not isinstance(action, dict):
            try:
                action = dict(action)
            except Exception as exc:
                raise ValueError(f"Workflow action {index + 1} must be an object") from exc

        if not isinstance(action, dict):
            raise ValueError(f"Workflow action {index + 1} must be an object")

        normalized = dict(action)
        action_type = normalized.get("type")
        if not isinstance(action_type, str) or not action_type.strip():
            raise ValueError(f"Workflow action {index + 1} is missing a type")

        normalized["type"] = action_type.strip()

        action_id = normalized.get("id")
        if not isinstance(action_id, str) or not action_id.strip():
            normalized["id"] = f"action_{index}"
        else:
            normalized["id"] = action_id.strip()

        action_name = normalized.get("name")
        if not isinstance(action_name, str) or not action_name.strip():
            normalized["name"] = normalized["id"]
        else:
            normalized["name"] = action_name.strip()

        params = normalized.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            try:
                params = dict(params)
            except Exception as exc:
                raise ValueError(f"Workflow action {index + 1} params must be an object") from exc
        if not isinstance(params, dict):
            raise ValueError(f"Workflow action {index + 1} params must be an object")
        normalized["params"] = params

        validate_action_params(normalized["type"], params, action_name=f"Workflow action {index + 1}")

        trigger = normalized.get("trigger")
        if trigger is not None and not isinstance(trigger, dict):
            try:
                trigger = dict(trigger)
            except Exception as exc:
                raise ValueError(f"Workflow action {index + 1} trigger must be an object") from exc
            if not isinstance(trigger, dict):
                raise ValueError(f"Workflow action {index + 1} trigger must be an object")

        if trigger is None:
            normalized.pop("trigger", None)
        else:
            normalized["trigger"] = trigger

        description = normalized.get("description")
        if description is not None:
            normalized["description"] = str(description)

        return normalized

    def _write_workflow_file_atomic(self, workflow_path: str, workflow_data: dict[str, Any]) -> None:
        os.makedirs(self._catalog.workflows_dir, exist_ok=True)
        file_descriptor, temp_path = tempfile.mkstemp(
            prefix="workflow_",
            suffix=".tmp",
            dir=self._catalog.workflows_dir,
            text=True,
        )

        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
                yaml.dump(
                    workflow_data,
                    handle,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=2,
                    width=120,
                )
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temp_path, workflow_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
