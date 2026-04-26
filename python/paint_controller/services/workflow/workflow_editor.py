"""QML-facing workflow editor persistence boundary."""

from __future__ import annotations

import json
import os

import yaml
from PySide6.QtCore import QObject, Property, Signal, Slot

from .workflow_catalog import WorkflowCatalog


class WorkflowEditor(QObject):
    """Own workflow file read/write/delete operations for the editor surface."""

    workflow_list_changed = Signal()
    error_occurred = Signal(str)

    def __init__(self, catalog: WorkflowCatalog, logger, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._logger = logger
        self._catalog.workflow_list_changed.connect(self.workflow_list_changed.emit)

    @Property(list, notify=workflow_list_changed)
    def workflow_list(self) -> list[str]:
        return self._catalog.workflow_list

    @Slot()
    def refresh_workflow_list(self) -> None:
        self._catalog.refresh_workflow_list()

    @Slot(str, result=str)
    def get_workflow_data(self, workflow_name: str) -> str:
        if not self._catalog.contains(workflow_name):
            self._logger.error(f"WorkFlow not found: {workflow_name}")
            return ""

        workflow_path = self._catalog.resolve_workflow_path(workflow_name)
        if workflow_path is None:
            self._logger.error(f"WorkFlow file not found: {workflow_name}")
            return ""

        try:
            with open(workflow_path, "r", encoding="utf-8") as handle:
                workflow_data = yaml.safe_load(handle)
            return json.dumps(workflow_data)
        except Exception as exc:
            self._logger.error(f"Error loading workflow data: {exc}")
            return ""

    @Slot(str, str, result=bool)
    def save_workflow_data(self, workflow_name: str, workflow_json: str) -> bool:
        try:
            workflow_data = json.loads(workflow_json)
            workflow_data["name"] = workflow_name

            workflow_path = os.path.join(self._catalog.workflows_dir, f"{workflow_name}.yaml")
            with open(workflow_path, "w", encoding="utf-8") as handle:
                yaml.dump(
                    workflow_data,
                    handle,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=2,
                    width=120,
                )

            self._logger.info(f"Saved workflow: {workflow_path}")
            self._catalog.refresh_workflow_list()
            return True
        except Exception as exc:
            error_msg = f"Error saving workflow: {exc}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    @Slot(str, result=bool)
    def delete_workflow(self, workflow_name: str) -> bool:
        if not self._catalog.contains(workflow_name):
            error_msg = f"WorkFlow not found: {workflow_name}"
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