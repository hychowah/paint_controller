"""QML-facing workflow editor session: document mutations, dirty, save/load."""

from __future__ import annotations

import os
import tempfile
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import yaml
from PySide6.QtCore import Property, QObject, Signal, Slot

from .action_schema import member_palette_entries, param_fields_for_type
from .document import (
    CONTINUE_IMMEDIATELY,
    CONTINUE_WAIT_COMPLETE,
    KIND_ACTION,
    KIND_PARALLEL,
    KIND_WAIT,
    SCHEMA_VERSION,
    ActionMember,
    WorkflowDocument,
    WorkflowStep,
    default_params_for_type,
    palette_entries,
)
from .document_migrate import migrate_raw_to_document
from .workflow_catalog import WorkflowCatalog

if TYPE_CHECKING:
    from .workflow_runner import WorkFlowRunner


class WorkflowEditor(QObject):
    """Own the open editor session and workflow file persistence."""

    workflow_list_changed = Signal()
    error_occurred = Signal(str)
    document_changed = Signal()
    dirty_changed = Signal(bool)
    selected_index_changed = Signal(int)
    selected_member_index_changed = Signal(int)
    is_open_changed = Signal(bool)
    loop_changed = Signal(bool)
    name_changed = Signal(str)

    def __init__(self, catalog: WorkflowCatalog, logger, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._logger = logger
        self._runner: WorkFlowRunner | None = None
        self._catalog.workflow_list_changed.connect(self.workflow_list_changed.emit)

        self._is_open = False
        self._dirty = False
        self._selected_index = -1
        self._selected_member_index = -1
        self._document = WorkflowDocument.empty("untitled")
        self._loaded_name = ""  # catalog name currently associated with disk

    def attach_runtime(self, runner: WorkFlowRunner) -> None:
        """Attach the runtime owner so editor mutations follow runtime collision rules."""
        self._runner = runner

    # --- visibility ---

    @Property(bool, notify=is_open_changed)
    def is_open(self) -> bool:
        return self._is_open

    @Slot(result=bool)
    def open_editor(self) -> bool:
        """Open the full-page editor; start empty session if none loaded."""
        self._is_open = True
        self.is_open_changed.emit(True)
        if not self._loaded_name and not self._document.steps:
            self.new_document("untitled")
        return True

    @Slot(result=bool)
    def close_editor(self) -> bool:
        """Close the full-page editor (does not auto-save)."""
        self._is_open = False
        self.is_open_changed.emit(False)
        return True

    # --- catalog ---

    @Property(list, notify=workflow_list_changed)
    def workflow_list(self) -> list[str]:
        names = self._catalog.workflow_list
        return list(names) if not callable(names) else list(names())

    @Slot()
    def refresh_workflow_list(self) -> None:
        self._catalog.refresh_workflow_list()

    # --- document properties ---

    @Property(bool, notify=dirty_changed)
    def is_dirty(self) -> bool:
        return self._dirty

    @Property(str, notify=name_changed)
    def workflow_name(self) -> str:
        return self._document.name

    @Property(str, notify=document_changed)
    def description(self) -> str:
        return self._document.description

    @Property(bool, notify=loop_changed)
    def loop(self) -> bool:
        return self._document.loop

    @Property(list, notify=document_changed)
    def steps(self) -> list[dict[str, Any]]:
        return self._document.steps_as_qml_list()

    @Property(int, notify=selected_index_changed)
    def selected_index(self) -> int:
        return self._selected_index

    @Property(int, notify=selected_member_index_changed)
    def selected_member_index(self) -> int:
        return self._selected_member_index

    @Property(list, constant=True)
    def palette(self) -> list[dict[str, Any]]:
        return palette_entries()

    @Property(list, constant=True)
    def member_palette(self) -> list[dict[str, Any]]:
        """Action types legal as parallel members (no wait / structural parallel)."""
        return member_palette_entries()

    @Slot(str, result="QVariant")
    def param_fields(self, action_type: str) -> list[dict[str, Any]]:
        """Schema-driven editor fields for an action type (QML presentation only)."""
        return param_fields_for_type(action_type or "")

    @Property("QVariant", notify=document_changed)
    def document(self) -> dict[str, Any]:
        return self._document.to_qml_map()

    def _set_dirty(self, dirty: bool) -> None:
        if dirty == self._dirty:
            return
        self._dirty = dirty
        self.dirty_changed.emit(dirty)

    def _emit_document(self) -> None:
        self.document_changed.emit()
        self.name_changed.emit(self._document.name)
        self.loop_changed.emit(self._document.loop)

    def _set_selected_member_index(self, index: int) -> None:
        if index == self._selected_member_index:
            return
        self._selected_member_index = index
        self.selected_member_index_changed.emit(index)

    def _selected_parallel_step(self) -> WorkflowStep | None:
        if self._selected_index < 0 or self._selected_index >= len(self._document.steps):
            return None
        step = self._document.steps[self._selected_index]
        if step.kind != KIND_PARALLEL:
            return None
        return step

    def _sync_member_selection_for_step(self) -> None:
        """Clamp or reset member selection based on the currently selected step."""
        step = self._selected_parallel_step()
        if step is None or not step.members:
            self._set_selected_member_index(-1)
            return
        if self._selected_member_index < 0 or self._selected_member_index >= len(step.members):
            self._set_selected_member_index(0)

    def _legal_member_types(self) -> set[str]:
        return {str(entry["type"]) for entry in member_palette_entries() if entry.get("type")}

    def _make_member(self, action_type: str, *, reserved: set[str] | None = None) -> ActionMember:
        action_type = (action_type or "").strip()
        if not action_type or action_type not in self._legal_member_types():
            raise ValueError(f"Illegal parallel member type: {action_type!r}")
        member_id = self._allocate_id("m", reserved=reserved)
        return ActionMember(
            id=member_id,
            type=action_type,
            params=default_params_for_type(action_type),
        )

    def _replace_document(self, document: WorkflowDocument, *, loaded_name: str, dirty: bool) -> None:
        self._document = document
        self._loaded_name = loaded_name
        self._selected_index = -1
        self.selected_index_changed.emit(self._selected_index)
        self._set_selected_member_index(-1)
        self._set_dirty(dirty)
        self._emit_document()

    # --- session mutations ---

    @Slot(str)
    def new_document(self, name: str = "untitled") -> None:
        clean = (name or "untitled").strip() or "untitled"
        self._replace_document(WorkflowDocument.empty(clean), loaded_name="", dirty=True)

    @Slot(int)
    def select_step(self, index: int) -> None:
        if index < -1 or index >= len(self._document.steps):
            index = -1
        if index == self._selected_index:
            return
        self._selected_index = index
        self.selected_index_changed.emit(index)
        step = self._selected_parallel_step()
        if step is not None and step.members:
            self._set_selected_member_index(0)
        else:
            self._set_selected_member_index(-1)

    @Slot(bool)
    def set_loop(self, enabled: bool) -> None:
        self._document.loop = bool(enabled)
        self._set_dirty(True)
        self.loop_changed.emit(self._document.loop)
        self.document_changed.emit()

    @Slot(str)
    def set_description(self, description: str) -> None:
        self._document.description = str(description or "")
        self._set_dirty(True)
        self.document_changed.emit()

    @Slot(str)
    def set_workflow_name(self, name: str) -> None:
        clean = (name or "").strip()
        if not clean:
            return
        self._document.name = clean
        self._set_dirty(True)
        self.name_changed.emit(clean)
        self.document_changed.emit()

    @Slot(str, result=bool)
    def add_step(self, palette_type: str) -> bool:
        """Add a step from the palette after the selection (or at end)."""
        try:
            step = self._make_step_from_palette(palette_type)
            insert_at = self._selected_index + 1 if self._selected_index >= 0 else len(self._document.steps)
            self._document.steps.insert(insert_at, step)
            self._document.validate()
            self._selected_index = insert_at
            self._set_dirty(True)
            self._emit_document()
            self.selected_index_changed.emit(self._selected_index)
            if step.kind == KIND_PARALLEL and step.members:
                self._set_selected_member_index(0)
            else:
                self._set_selected_member_index(-1)
            return True
        except Exception as exc:
            self._emit_error(f"Cannot add step: {exc}")
            return False

    def _make_step_from_palette(self, palette_type: str) -> WorkflowStep:
        palette_type = (palette_type or "").strip()
        step_id = self._allocate_id("step")
        if palette_type == "time_wait" or palette_type == KIND_WAIT:
            return WorkflowStep(id=step_id, kind=KIND_WAIT, duration_ms=1000)
        if palette_type == "parallel" or palette_type == KIND_PARALLEL:
            reserved = {step_id}
            m1_id = self._allocate_id("m", reserved=reserved)
            reserved.add(m1_id)
            m2_id = self._allocate_id("m", reserved=reserved)
            m1 = ActionMember(
                id=m1_id,
                type="valve_turn",
                params=default_params_for_type("valve_turn"),
            )
            m2 = ActionMember(
                id=m2_id,
                type="spray_gimbal",
                params=default_params_for_type("spray_gimbal"),
            )
            return WorkflowStep(
                id=step_id,
                kind=KIND_PARALLEL,
                continue_policy=CONTINUE_WAIT_COMPLETE,
                members=[m1, m2],
            )
        params = default_params_for_type(palette_type)
        return WorkflowStep(
            id=step_id,
            kind=KIND_ACTION,
            type=palette_type,
            params=params,
            continue_policy=CONTINUE_WAIT_COMPLETE,
        )

    def _allocate_id(self, prefix: str, *, reserved: set[str] | None = None) -> str:
        existing: set[str] = set(reserved or ())
        for step in self._document.steps:
            existing.add(step.id)
            for member in step.members:
                existing.add(member.id)
        n = 0
        while True:
            candidate = f"{prefix}_{n:02d}" if prefix == "step" else f"{prefix}{n}"
            if candidate not in existing:
                return candidate
            n += 1

    @Slot(result=bool)
    def remove_selected_step(self) -> bool:
        if self._selected_index < 0 or self._selected_index >= len(self._document.steps):
            return False
        del self._document.steps[self._selected_index]
        if self._selected_index >= len(self._document.steps):
            self._selected_index = len(self._document.steps) - 1
        self._set_dirty(True)
        self._emit_document()
        self.selected_index_changed.emit(self._selected_index)
        self._sync_member_selection_for_step()
        return True

    @Slot(result=bool)
    def move_selected_up(self) -> bool:
        idx = self._selected_index
        if idx <= 0:
            return False
        steps = self._document.steps
        steps[idx - 1], steps[idx] = steps[idx], steps[idx - 1]
        self._selected_index = idx - 1
        self._set_dirty(True)
        self._emit_document()
        self.selected_index_changed.emit(self._selected_index)
        return True

    @Slot(result=bool)
    def move_selected_down(self) -> bool:
        idx = self._selected_index
        if idx < 0 or idx >= len(self._document.steps) - 1:
            return False
        steps = self._document.steps
        steps[idx + 1], steps[idx] = steps[idx], steps[idx + 1]
        self._selected_index = idx + 1
        self._set_dirty(True)
        self._emit_document()
        self.selected_index_changed.emit(self._selected_index)
        return True

    @Slot(str, result=bool)
    def set_continue_policy(self, policy: str) -> bool:
        if self._selected_index < 0:
            return False
        if policy not in (CONTINUE_WAIT_COMPLETE, CONTINUE_IMMEDIATELY):
            self._emit_error(f"Invalid continue policy: {policy}")
            return False
        step = self._document.steps[self._selected_index]
        if step.kind not in (KIND_ACTION, KIND_PARALLEL):
            return False
        step.continue_policy = policy
        self._set_dirty(True)
        self.document_changed.emit()
        return True

    @Slot(int, result=bool)
    def set_wait_duration_ms(self, duration_ms: int) -> bool:
        if self._selected_index < 0:
            return False
        step = self._document.steps[self._selected_index]
        if step.kind != KIND_WAIT:
            return False
        if int(duration_ms) <= 0:
            self._emit_error("duration_ms must be > 0")
            return False
        step.duration_ms = int(duration_ms)
        self._set_dirty(True)
        self.document_changed.emit()
        return True

    @Slot(str, "QVariant", result=bool)
    def set_param(self, key: str, value: Any) -> bool:
        """Set a param on the selected action step (not parallel members)."""
        if self._selected_index < 0:
            return False
        step = self._document.steps[self._selected_index]
        try:
            if step.kind == KIND_ACTION:
                step.params[key] = self._coerce_param_value(value)
                self._document.validate()
            elif step.kind == KIND_WAIT and key == "duration_ms":
                return self.set_wait_duration_ms(int(value))
            else:
                # Parallel and other kinds must use set_member_param / dedicated slots.
                return False
            self._set_dirty(True)
            self.document_changed.emit()
            return True
        except Exception as exc:
            self._emit_error(str(exc))
            return False

    @Slot(int, str, "QVariant", result=bool)
    def set_member_param(self, member_index: int, key: str, value: Any) -> bool:
        if self._selected_index < 0:
            return False
        step = self._document.steps[self._selected_index]
        if step.kind != KIND_PARALLEL:
            return False
        if member_index < 0 or member_index >= len(step.members):
            return False
        try:
            step.members[member_index].params[key] = self._coerce_param_value(value)
            self._document.validate()
            self._set_dirty(True)
            self.document_changed.emit()
            return True
        except Exception as exc:
            self._emit_error(str(exc))
            return False

    @Slot(int)
    def select_member(self, index: int) -> None:
        step = self._selected_parallel_step()
        if step is None or not step.members:
            self._set_selected_member_index(-1)
            return
        if index < 0 or index >= len(step.members):
            return
        self._set_selected_member_index(index)

    @Slot(str, result=bool)
    def add_member(self, action_type: str) -> bool:
        step = self._selected_parallel_step()
        if step is None:
            self._emit_error("No parallel step selected")
            return False
        try:
            member = self._make_member(action_type)
            step.members.append(member)
            self._document.validate()
            self._set_dirty(True)
            self._emit_document()
            self._set_selected_member_index(len(step.members) - 1)
            return True
        except Exception as exc:
            self._emit_error(f"Cannot add member: {exc}")
            return False

    @Slot(result=bool)
    def remove_selected_member(self) -> bool:
        step = self._selected_parallel_step()
        if step is None:
            return False
        if len(step.members) <= 1:
            self._emit_error("Parallel group requires at least one member")
            return False
        idx = self._selected_member_index
        if idx < 0 or idx >= len(step.members):
            return False
        del step.members[idx]
        if idx >= len(step.members):
            idx = len(step.members) - 1
        self._set_dirty(True)
        self._emit_document()
        self._set_selected_member_index(idx)
        return True

    @Slot(str, result=bool)
    def set_member_type(self, action_type: str) -> bool:
        step = self._selected_parallel_step()
        if step is None:
            return False
        idx = self._selected_member_index
        if idx < 0 or idx >= len(step.members):
            self._emit_error("No parallel member selected")
            return False
        action_type = (action_type or "").strip()
        if not action_type or action_type not in self._legal_member_types():
            self._emit_error(f"Illegal parallel member type: {action_type!r}")
            return False
        try:
            member = step.members[idx]
            member.type = action_type
            member.params = default_params_for_type(action_type)
            # Keep member.id and any reserved advanced timing.
            self._document.validate()
            self._set_dirty(True)
            self._emit_document()
            return True
        except Exception as exc:
            self._emit_error(str(exc))
            return False

    @Slot(result=bool)
    def move_selected_member_up(self) -> bool:
        step = self._selected_parallel_step()
        if step is None:
            return False
        idx = self._selected_member_index
        if idx <= 0 or idx >= len(step.members):
            return False
        members = step.members
        members[idx - 1], members[idx] = members[idx], members[idx - 1]
        self._set_dirty(True)
        self._emit_document()
        self._set_selected_member_index(idx - 1)
        return True

    @Slot(result=bool)
    def move_selected_member_down(self) -> bool:
        step = self._selected_parallel_step()
        if step is None:
            return False
        idx = self._selected_member_index
        if idx < 0 or idx >= len(step.members) - 1:
            return False
        members = step.members
        members[idx + 1], members[idx] = members[idx], members[idx + 1]
        self._set_dirty(True)
        self._emit_document()
        self._set_selected_member_index(idx + 1)
        return True

    @staticmethod
    def _coerce_param_value(value: Any) -> Any:
        # QML often sends floats for whole numbers.
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value

    # --- load / save ---

    @Slot(str, result="QVariant")
    def load_document(self, workflow_name: str) -> dict[str, Any]:
        """Load a workflow into the editor session. Returns document map or {}."""
        if not self._catalog.contains(workflow_name):
            self._emit_error(f"WorkFlow not found: {workflow_name}")
            return {}

        workflow_path = self._catalog.resolve_workflow_path(workflow_name)
        if workflow_path is None:
            self._emit_error(f"WorkFlow file not found: {workflow_name}")
            return {}

        try:
            with open(workflow_path, encoding="utf-8") as handle:
                raw = yaml.safe_load(handle)
            document = migrate_raw_to_document(raw, default_name=workflow_name)
            self._replace_document(document, loaded_name=workflow_name, dirty=False)
            return self._document.to_qml_map()
        except Exception as exc:
            self._emit_error(f"Error loading workflow data: {exc}")
            return {}

    @Slot(result=bool)
    def save(self) -> bool:
        """Save the current session document under its name."""
        return self._persist_current(self._document.name)

    @Slot(str, result=bool)
    def save_as(self, workflow_name: str) -> bool:
        name = (workflow_name or "").strip()
        if not name:
            self._emit_error("Workflow name is required")
            return False
        self._document.name = name
        return self._persist_current(name)

    @Slot(str, str, bool, list, result=bool)
    def save_document(
        self,
        workflow_name: str,
        description: str,
        loop: bool,
        actions_or_steps: list,
    ) -> bool:
        """Compatibility/save path: accept v2 steps list or legacy actions list."""
        try:
            raw: dict[str, Any] = {
                "name": workflow_name,
                "description": description,
                "loop": bool(loop),
            }
            # Heuristic: v2 steps have kind; legacy actions have type without kind.
            items = list(actions_or_steps) if actions_or_steps is not None else []
            if items and isinstance(items[0], dict) and items[0].get("kind"):
                raw["schema_version"] = SCHEMA_VERSION
                raw["steps"] = [self._coerce_plain(item) for item in items]
                document = WorkflowDocument.from_dict(raw, default_name=workflow_name)
            else:
                raw["actions"] = [self._coerce_plain(item) for item in items]
                document = migrate_raw_to_document(raw, default_name=workflow_name)

            self._document = document
            return self._persist_current(workflow_name)
        except Exception as exc:
            self._emit_error(f"Error saving workflow: {exc}")
            return False

    @Slot(str, result=bool)
    def delete_workflow(self, workflow_name: str) -> bool:
        if not self._catalog.contains(workflow_name):
            self._emit_error(f"WorkFlow not found: {workflow_name}")
            return False

        if self._runner is not None:
            allowed, error_msg = self._runner.can_delete_workflow_document(workflow_name)
            if not allowed:
                assert error_msg is not None
                self._emit_error(error_msg)
                return False

        workflow_path = self._catalog.resolve_workflow_path(workflow_name)
        if workflow_path is None:
            self._emit_error(f"WorkFlow file not found: {workflow_name}")
            return False

        try:
            os.remove(workflow_path)
            self._logger.info(f"Deleted workflow: {workflow_path}")
            if self._loaded_name == workflow_name:
                self.new_document("untitled")
                self._set_dirty(False)
            self._catalog.refresh_workflow_list()
            return True
        except Exception as exc:
            self._emit_error(f"Error deleting workflow: {exc}")
            return False

    def _persist_current(self, workflow_name: str) -> bool:
        try:
            if self._runner is not None:
                allowed, error_msg = self._runner.can_save_workflow_document(workflow_name)
                if not allowed:
                    assert error_msg is not None
                    self._emit_error(error_msg)
                    return False

            self._document.name = workflow_name
            self._document.validate()
            payload = self._document.to_dict()

            existing_path = self._catalog.resolve_workflow_path(workflow_name)
            if existing_path is not None:
                workflow_path = existing_path
            else:
                workflow_path = os.path.join(self._catalog.workflows_dir, f"{workflow_name}.yaml")

            self._write_workflow_file_atomic(workflow_path, payload)
            self._logger.info(f"Saved workflow: {workflow_path}")
            self._loaded_name = workflow_name
            self._set_dirty(False)
            self._catalog.refresh_workflow_list()
            if self._runner is not None:
                self._runner.mark_workflow_document_saved(workflow_name)
            self._emit_document()
            return True
        except Exception as exc:
            self._emit_error(f"Error saving workflow: {exc}")
            return False

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

    def _coerce_plain(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, dict):
            return {k: self._coerce_plain(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._coerce_plain(v) for v in value]
        try:
            # QVariantMap / nested Qt containers
            if hasattr(value, "items"):
                return {k: self._coerce_plain(v) for k, v in dict(value).items()}
        except Exception:
            pass
        return value

    def _emit_error(self, message: str) -> None:
        self._logger.error(message)
        self.error_occurred.emit(message)

    # Used by preserve-on-edit tests / advanced tools
    def get_internal_document(self) -> WorkflowDocument:
        return deepcopy(self._document)  # type: ignore[return-value]
