"""Shared workflow catalog ownership for runtime and editor surfaces."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PySide6.QtCore import QFileSystemWatcher, QObject, Property, Signal, Slot


class WorkflowCatalog(QObject):
    """Own the workflow directory, file watching, and available workflow names."""

    workflow_list_changed = Signal()

    def __init__(self, workflows_dir: str | None = None, logger=None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.logger = logger
        self._workflow_list: List[str] = []
        self._workflows_dir = workflows_dir or self._find_workflows_dir()

        self._file_watcher = QFileSystemWatcher(self)
        self._file_watcher.addPath(self._workflows_dir)
        self._file_watcher.directoryChanged.connect(self._on_directory_changed)

        self.refresh_workflow_list()

    def _find_workflows_dir(self) -> str:
        """Find workflows directory relative to package."""
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "resource", "workflows"),
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resource", "workflows"
            ),
            "./workflows",
        ]

        for path in possible_paths:
            if os.path.isdir(path):
                if self.logger is not None:
                    self.logger.info(f"Found workflows directory: {path}")
                return path

        default_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "..", "resource", "workflows"
        )
        os.makedirs(default_path, exist_ok=True)
        if self.logger is not None:
            self.logger.warning(f"Created workflows directory: {default_path}")
        return default_path

    @Property(list, notify=workflow_list_changed)
    def workflow_list(self) -> List[str]:
        """Get list of available workflow names."""
        return self._workflow_list

    @property
    def workflows_dir(self) -> str:
        return self._workflows_dir

    def contains(self, workflow_name: str) -> bool:
        return workflow_name in self._workflow_list

    def resolve_workflow_path(self, workflow_name: str) -> str | None:
        yaml_path = os.path.join(self._workflows_dir, f"{workflow_name}.yaml")
        if os.path.exists(yaml_path):
            return yaml_path

        yml_path = os.path.join(self._workflows_dir, f"{workflow_name}.yml")
        if os.path.exists(yml_path):
            return yml_path

        return None

    def _on_directory_changed(self, path: str) -> None:
        if self.logger is not None:
            self.logger.info(f"WorkFlow directory changed: {path}")
        self.refresh_workflow_list()

    @Slot()
    def refresh_workflow_list(self) -> None:
        """Refresh list of available workflows from disk."""
        try:
            workflow_names = {
                Path(filename).stem
                for filename in os.listdir(self._workflows_dir)
                if filename.endswith(".yaml") or filename.endswith(".yml")
            }
            new_list = sorted(workflow_names, key=lambda name: (name.casefold(), name))

            if new_list != self._workflow_list:
                self._workflow_list = new_list
                if self.logger is not None:
                    self.logger.info(f"WorkFlow list updated: {len(self._workflow_list)} workflows found")
                self.workflow_list_changed.emit()
        except Exception as exc:
            if self.logger is not None:
                self.logger.error(f"Error refreshing workflow list: {exc}")
            self._workflow_list = []

    def cleanup(self) -> None:
        self._file_watcher.deleteLater()