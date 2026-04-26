# Architecture Progress

Status board for the active architecture roadmap in `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`.

Use this file for current stage status and next-slice tracking.
Use `DEVNOTES.md` for verified implementation history.
Use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for the architecture rationale and staged roadmap.

## Current State

- Overall status: in progress
- Most recent completed slice: Stage 2 selection-model extraction
- Last completed implementation slice: Stage 2 selection-model extraction
- Next recommended slice: Continue Stage 2 by reducing remaining overlay facade responsibility now that selection ownership is extracted
- Linux validation status: complete after rebasing onto `refactor`
- Last focused validation: focused Stage 2 ownership and regression slices are green for `tests/test_joystick_selection.py`, `tests/test_control_processor.py`, `tests/test_input_handler.py`, `tests/test_controller_factory_runtime.py`, `tests/test_safety_integration.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`
- Latest full validation: `196 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`

## Stage Board

| Stage | Status | Notes |
|---|---|---|
| Stage 0 | completed | Durable authority map is now published in this tracker |
| Stage 1 | completed | Stage 1A through Stage 1E boundary freezes are implemented and validated |
| Stage 2 | in progress | The live cycle is removed and joystick selection ownership now lives in a dedicated model; remaining cleanup is about narrowing the overlay facade and finishing ownership boundaries |
| Stage 3 | not started | `ShellState` split for the two-surface shell; route cleanup folded into the same stage |
| Stage 4 | not started | Settings authority, capability classes, and role-based surfaces |
| Stage 5 | not started | Operational overlay contract |
| Stage 6 | not started | Workflow stabilization and conditional behavior-tree readiness |
| Stage 7 | not started | Narrower QML contract after owners are clear |
| Stage 8 | not started | Optional feature-shell recomposition |
| Stage 9 | not started | Design-system cleanup |

## Baseline Authority Map

| Area | Current primary owner | Adjacent / duplicate owners | Notes |
|---|---|---|---|
| Shell window composition | `python/paint_controller/qml/core/MainWindow.qml` | `python/paint_controller/qml/overlays/MultiScreenListUI.qml` | Root QML still owns page construction, overlay composition, and secondary-window creation |
| Screen facts vs product policy | `python/paint_controller/services/screen_manager.py` for screen facts | `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/core/qt_bridge.py` | Screen discovery is already in Python, but product policy is still partly invented in QML and triggered through bridge calls |
| Route identity and selection | `MainWindow.qml` page registry | `python/paint_controller/qml/navigation/SelectBar.qml` | Registry exists, but button catalog and selection behavior are still duplicated in QML |
| Overlay visibility and active-menu policy | `python/paint_controller/ui/overlay.py` | `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`, `MainWindow.qml`, `MultiScreenListUI.qml` | Overlay state is global Python state interpreted differently by multiple QML surfaces |
| Control selection vs command execution | `python/paint_controller/models/joystick_selection.py` for selection state | `python/paint_controller/ui/overlay.py`, `python/paint_controller/handlers/input.py`, `python/paint_controller/handlers/control_processor.py` | Selection ownership is extracted; `OverlayController` now acts as the compatibility/presentation facade |
| Settings authority | `python/paint_controller/core/settings.py` | `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`, `python/paint_controller/qml/pages/settings/PageSettings.qml` | Python is authoritative; the overlay is the live consumer; the page tree is still transitional |
| Workflow runtime | `python/paint_controller/services/workflow/workflow_runner.py` | `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`, `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml` | Runtime control and status stay on `workFlowRunner`, now backed by a shared catalog and guarded execution transitions |
| Workflow persistence | `python/paint_controller/services/workflow/workflow_editor.py` | `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml` | Editor persistence is now split away from runtime execution and shares catalog ownership through `workflow_catalog.py` |
| Machine-affecting QML actions | `python/paint_controller/handlers/manual_commands.py`, `python/paint_controller/handlers/device_actions.py`, `python/paint_controller/handlers/device_operations.py`, `python/paint_controller/services/workflow/workflow_runner.py` | `SettingsTab.qml`, `WorkFlowTab.qml`, `EditWorkFlowTab.qml` | The highest-risk direct mutators on the Stage 1 surfaces now route through Python-owned boundaries |

## Completed Slices

### 2026-04-25 - Stage 0 Authority Map Publication

- Published the durable ownership map for shell state, overlay visibility, control selection, settings, workflow runtime, workflow persistence, and direct machine-affecting QML paths.
- Locked the next code slice to Stage 1B hard device actions instead of the previously-stated settings-outlier path.
- Replaced the old shell-coordinator idea with the narrower `ScreenManager` facts + `ShellState` policy + `QtBridge` intents split in the active roadmap.

### 2026-04-25 - Stage 1A Manual Command Boundary Freeze

- Added Python-owned `ManualCommandHandler` and rewired `CommandTab.qml` to use it.
- Moved command validation, coercion, and dispatch out of QML.
- Kept unsupported commands visible but explicitly unavailable instead of silent no-ops.
- Fixed the Demo parameter mismatch by making Python consume the existing QML gimbal parameter names.

### 2026-04-26 - Stage 1B Through 1E Boundary Freeze

- Added `DeviceActionHandler` and `DeviceOperationsHandler`, then rewired `DeviceControlTab.qml` so hard device actions and operational side effects route through Python-owned boundaries.
- Split workflow editor persistence into `workflow_catalog.py` and `workflow_editor.py`, and rewired `EditWorkFlowTab.qml` to the new editor-facing boundary.
- Hardened `WorkFlowRunner` so runtime execution keeps the existing contract but rejects loading a new workflow while execution is active.
- Expanded direct handler/runtime/factory/startup coverage and reran the full suite to `190 passed`.

### 2026-04-26 - Stage 2 Initial Control-Selection Cycle Break

- Moved `EF Yaw Angle` selection-time offset seeding into `ControlProcessor` so the processor now owns its own yaw target transition behavior.
- Removed `OverlayController`'s `ControlProcessor` back-reference and deleted the deferred cycle wiring from `controller_factory.py`.
- Added focused control-processor transition tests and reran the Stage 2 regression slice plus the full suite to `193 passed`.

### 2026-04-26 - Stage 2 Selection Model Extraction

- Added `JoystickSelectionModel` as the dedicated owner of committed and temporary joystick selection state.
- Rewired `OverlayController` into a presentation/compatibility facade over that model and made `ControlProcessor` read the model directly.
- Added direct selection-model tests and reran the focused Stage 2 slices plus the full suite to `196 passed`.

## Active Risks

- The broad QML context-property contract remains intentionally additive; Stage 1 reduced direct side effects without yet reducing exposure count materially.
- Stage 2 is materially further along, but `OverlayController` still remains as a compatibility facade that mixes menu presentation with some selection-oriented methods.
- Shell and overlay policy work should still stay blocked on the rest of Stage 2 ownership cleanup.

## Next Session Checklist

1. Continue Stage 2 by narrowing `OverlayController` to overlay/menu presentation and reducing its remaining selection-oriented facade methods where practical.
2. Keep `docs/tech-debt.md` and this tracker in sync as Stage 2 advances so the remaining cleanup stays truthful.
3. Treat shell/overlay cleanup as blocked on the rest of Stage 2 unless the roadmap is explicitly reprioritized.