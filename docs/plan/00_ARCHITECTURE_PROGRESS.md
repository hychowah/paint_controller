# Architecture Progress

Status board for the active architecture roadmap in `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`.

Use this file for current stage status and next-slice tracking.
Use `DEVNOTES.md` for verified implementation history.
Use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for the architecture rationale and staged roadmap.

## Current State

- Overall status: in progress
- Most recent completed slice: Stage 4 settings truthfulness + capability model
- Last completed implementation slice: Stage 4 settings truthfulness + capability model
- Next recommended slice: Start Stage 3B1 route normalization by moving `MainWindow.qml` and `SelectBar.qml` onto one route manifest and one selected-route owner
- Linux validation status: complete after rebasing onto `refactor`
- Last focused validation: focused Stage 4 slices are green for `tests/test_capability_catalog.py`, `tests/test_controller_factory_runtime.py`, `tests/test_settings_runtime.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`
- Latest full validation: `210 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`

## Stage Board

| Stage | Status | Notes |
|---|---|---|
| Stage 0 | completed | Durable authority map is now published in this tracker |
| Stage 1 | completed | Command, device, and workflow boundary freezes are implemented and validated; the former Settings quick-apply exception was carried forward explicitly and is now closed by Stage 4 |
| Stage 2 | completed | The live cycle is removed, joystick selection ownership lives in a dedicated model, per-mode preset memory is selection-owned, direct overlay compatibility regressions exist, and the dead overlay compatibility wrappers are trimmed |
| Stage 3 | in progress | Stage 3A shell policy is complete; the next Stage 3 work is Stage 3B1 route normalization now that Stage 4 is complete |
| Stage 4 | completed | The Settings route is now truthful for schema-backed mixed-admin settings, camera remains explicit summary-only, and `CapabilityCatalog` publishes executable settings/admin metadata for later route and overlay slices |
| Stage 5 | not started | Next after shell and workflow slices: Stage 5A overlay hosting/layering, then Stage 5B operator-action legality |
| Stage 6 | not started | Stage 6A current workflow public-model stabilization, then Stage 6B behavior-tree preparation |
| Stage 7 | not started | Incremental QML-contract narrowing after owners are clear |
| Stage 8 | not started | Optional feature-shell recomposition |
| Stage 9 | not started | Design-system cleanup |

## Baseline Authority Map

| Area | Current primary owner | Adjacent / duplicate owners | Notes |
|---|---|---|---|
| Shell window composition | `python/paint_controller/qml/core/MainWindow.qml` | `python/paint_controller/qml/overlays/MultiScreenListUI.qml`, `python/paint_controller/models/shell_state.py` | QML still composes the windows, but screen-role and secondary-surface policy now flow from `ShellState` instead of being invented locally |
| Screen facts vs product policy | `python/paint_controller/services/screen_manager.py` for screen facts | `python/paint_controller/models/shell_state.py`, `python/paint_controller/core/qt_bridge.py` | Screen discovery remains fact-only in Python, and product shell policy now lives in `ShellState` rather than root QML |
| Route identity and selection | `MainWindow.qml` page registry | `python/paint_controller/qml/navigation/SelectBar.qml` | Registry exists, but button catalog and selection behavior are still duplicated in QML |
| Overlay visibility and active-menu policy | `python/paint_controller/ui/overlay.py` | `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`, `MainWindow.qml`, `MultiScreenListUI.qml` | Overlay/menu presentation is now a stable Python-owned facade consumed by multiple QML surfaces; the next shell work is about host-surface policy, not unresolved Stage 2 menu ownership |
| Control selection vs command execution | `python/paint_controller/models/joystick_selection.py` for selection state | `python/paint_controller/ui/overlay.py`, `python/paint_controller/handlers/control_processor.py` | Selection ownership is explicit, `OverlayController` is now a presentation facade, and `UIInputHandler` no longer stores long-term preset state |
| Settings authority | `python/paint_controller/core/settings.py` | `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`, `python/paint_controller/qml/pages/settings/PageSettings.qml`, `python/paint_controller/models/capability_catalog.py` | Python is authoritative; the Settings route now exposes schema-backed mixed-admin settings where a truthful contract exists, and `CapabilityCatalog` publishes executable metadata for settings/admin surfaces |
| Workflow runtime | `python/paint_controller/services/workflow/workflow_runner.py` | `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`, `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml` | Runtime control and status stay on `workFlowRunner`, now backed by a shared catalog and guarded execution transitions |
| Workflow persistence | `python/paint_controller/services/workflow/workflow_editor.py` | `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml` | Editor persistence is now split away from runtime execution and shares catalog ownership through `workflow_catalog.py` |
| Machine-affecting QML actions | `python/paint_controller/handlers/manual_commands.py`, `python/paint_controller/handlers/device_actions.py`, `python/paint_controller/handlers/device_operations.py`, `python/paint_controller/services/workflow/workflow_runner.py` | `python/paint_controller/qml/overlays/video/components/BaseTopViewSettingsPopup.qml`, `python/paint_controller/qml/pages/tuning/PageTuning.qml`, `python/paint_controller/qml/pages/status/PageStatus.qml`, `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`, `WorkFlowTab.qml`, `EditWorkFlowTab.qml` | The highest-risk command, device, and workflow mutators already route through Python-owned boundaries, and the remaining direct admin/calibration actions are now explicitly inventoried through `CapabilityCatalog` for later legality work |

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
- The remaining Settings quick-apply truthfulness gap is now tracked explicitly in the roadmap instead of being implicitly treated as closed Stage 1 work.

### 2026-04-26 - Stage 2 Initial Control-Selection Cycle Break

- Moved `EF Yaw Angle` selection-time offset seeding into `ControlProcessor` so the processor now owns its own yaw target transition behavior.
- Removed `OverlayController`'s `ControlProcessor` back-reference and deleted the deferred cycle wiring from `controller_factory.py`.
- Added focused control-processor transition tests and reran the Stage 2 regression slice plus the full suite to `193 passed`.

### 2026-04-26 - Stage 2 Selection Model Extraction

- Added `JoystickSelectionModel` as the dedicated owner of committed and temporary joystick selection state.
- Rewired `OverlayController` into a presentation/compatibility facade over that model and made `ControlProcessor` read the model directly.
- Added direct selection-model tests and reran the focused Stage 2 slices plus the full suite to `196 passed`.

### 2026-04-26 - Stage 2 Overlay/Input Ownership Freeze

- Added direct `OverlayController` compatibility regressions for menu visibility, temporary-vs-committed selection behavior, and yaw-reset handling.
- Moved base/EF preset memory into `JoystickSelectionModel`, removed the redundant input-side active-menu assignment, centralized overlay toggle behavior, and trimmed the dead overlay compatibility wrappers that no longer had live callers.
- Revalidated the focused overlay/input/startup slices and reran the full suite to `202 passed`.

### 2026-04-26 - Stage 3A Shell Policy Split

- Added a narrow `ShellState` owner for screen-role policy, secondary-surface presence, system-control host-surface policy, and fullscreen host policy.
- Registered `shellState` into the QML context and rewired `MainWindow.qml` plus `MultiScreenListUI.qml` to consume shell policy declaratively instead of turning raw screen count into product behavior locally.
- Added direct `ShellState` tests and reran the focused shell/startup/runtime slices to `26 passed`.

### 2026-04-26 - Stage 4A.1 Overlay Settings Authority Leak + Truthful Transitional Settings Route

- Removed the redundant direct `teensyController.thrust_force` mutation from `SettingsTab.qml`; the overlay thrust-force save path now routes through `settingsManager` only.
- Removed placeholder local state from `PageSettings.qml`, rewrote `MainSettingsPage.qml` summaries to stop claiming fake runtime values, and converted the unwired subpages into explicit transitional maintenance surfaces instead of fake-live controls.
- Wired the Settings subpage back buttons so they return to the top-level Settings page rather than rendering as dead affordances.
- Added a direct smoke test for `PageSettings.qml` and reran the focused Stage 4A.1 validation slices to `9 passed` for `tests/test_teensy.py` and `10 passed` for `tests/test_startup_smoke.py` plus `tests/test_qml_imports.py`.

### 2026-04-26 - Stage 4 Settings Truthfulness + Capability Model

- Added non-popup `apply*` slots in `SettingsManager` and a shared `ManagedSettingSpinBox.qml` helper so the Settings route can save schema-backed settings without fake placeholder controls or popup spam.
- Rewired the winch, wheels, arm, and main Settings pages to real schema-backed values, and kept the camera Settings page explicit about its summary-only role while base-top calibration remains overlay-primary.
- Added `CapabilityCatalog` as a thin Python-owned inventory for settings/admin capability and legality metadata, registered it in the runtime context, and pinned it with direct unit tests.
- Revalidated the focused Stage 4 slices to `27 passed` and reran the full suite to `210 passed`.

## Active Risks

- The broad QML context-property contract remains intentionally additive; Stage 1 reduced direct side effects without yet reducing exposure count materially.
- Route identity and selected-route ownership are still duplicated across `MainWindow.qml` and `SelectBar.qml`, and Stage 3B1 must normalize that before route semantics are formalized.
- `CapabilityCatalog` now inventories admin/calibration mutators, but later shell and overlay slices still need to decide where legality is enforced in UI behavior versus displayed as metadata.
- The broad QML context-property contract is now one property wider (`capabilityCatalog`) until later stages consume the metadata and retire older direct contracts.

## Next Session Checklist

1. Start Stage 3B1 by moving the route manifest and selected-route ownership onto one clear owner shared by `MainWindow.qml` and `SelectBar.qml`.
2. Keep the new `shellState` narrow; do not widen it into route metadata, settings authority, or a broad coordinator object while Stage 3B1 is in flight.
3. After Stage 3B1, use the new `CapabilityCatalog` to support later Stage 5B legality work rather than duplicating route/admin metadata in another surface-local model.
4. Keep `docs/tech-debt.md` and this tracker in sync as the roadmap returns from Stage 4 to the remaining Stage 3 and Stage 6 slices.