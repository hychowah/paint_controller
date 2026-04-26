# Architecture Progress

Status board for the active architecture roadmap in `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`.

Use this file for current stage status and next-slice tracking.
Use `DEVNOTES.md` for verified implementation history.
Use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for the architecture rationale and staged roadmap.

## Current State

- Overall status: in progress
- Most recent completed slice: Stage 3A shell policy split
- Last completed implementation slice: Stage 3A shell policy split
- Next recommended slice: Start Stage 4A settings truthfulness so Stage 3B route hardening has a legitimate Settings route to formalize
- Linux validation status: complete after rebasing onto `refactor`
- Last focused validation: focused Stage 3A shell-policy slices are green for `tests/test_shell_state.py`, `tests/test_startup_smoke.py`, `tests/test_services_runtime.py`, and `tests/test_qt_bridge.py`
- Latest full validation: `205 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`

## Stage Board

| Stage | Status | Notes |
|---|---|---|
| Stage 0 | completed | Durable authority map is now published in this tracker |
| Stage 1 | completed | Command, device, and workflow boundary freezes are implemented and validated; the remaining Settings quick-apply truthfulness gap is now carried explicitly into Stage 4A |
| Stage 2 | completed | The live cycle is removed, joystick selection ownership lives in a dedicated model, per-mode preset memory is selection-owned, direct overlay compatibility regressions exist, and the dead overlay compatibility wrappers are trimmed |
| Stage 3 | in progress | Stage 3A shell policy is complete; Stage 3B route hardening remains intentionally blocked until after Stage 4A settings truthfulness |
| Stage 4 | not started | Execute as Stage 4A settings truthfulness first, then Stage 4B broader settings authority/capability work |
| Stage 5 | not started | Overlay contract across system-control, joystick, emergency, and fullscreen HUD layers |
| Stage 6 | not started | Stage 6A current workflow stabilization, then Stage 6B behavior-tree preparation |
| Stage 7 | not started | Narrower QML contract after owners are clear |
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
| Settings authority | `python/paint_controller/core/settings.py` | `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`, `python/paint_controller/qml/pages/settings/PageSettings.qml` | Python is authoritative; the overlay is the live consumer; the page tree is still transitional |
| Workflow runtime | `python/paint_controller/services/workflow/workflow_runner.py` | `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`, `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml` | Runtime control and status stay on `workFlowRunner`, now backed by a shared catalog and guarded execution transitions |
| Workflow persistence | `python/paint_controller/services/workflow/workflow_editor.py` | `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml` | Editor persistence is now split away from runtime execution and shares catalog ownership through `workflow_catalog.py` |
| Machine-affecting QML actions | `python/paint_controller/handlers/manual_commands.py`, `python/paint_controller/handlers/device_actions.py`, `python/paint_controller/handlers/device_operations.py`, `python/paint_controller/services/workflow/workflow_runner.py` | `SettingsTab.qml`, `WorkFlowTab.qml`, `EditWorkFlowTab.qml` | The highest-risk command, device, and workflow mutators now route through Python-owned boundaries, but the remaining Settings quick-apply path is still a live exception |

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

## Active Risks

- The broad QML context-property contract remains intentionally additive; Stage 1 reduced direct side effects without yet reducing exposure count materially.
- The remaining Settings quick-apply path in `SettingsTab.qml` is explicitly unresolved and must be handled in Stage 4A.
- Stage 3B route hardening still depends on Stage 4A making the Settings route truthful enough to formalize.

## Next Session Checklist

1. Start Stage 4A by removing placeholder/local Settings-route state and making the Settings route truthful before route semantics are hardened.
2. Keep the new `shellState` narrow; do not widen it into route metadata, settings authority, or a broad coordinator object while Stage 4A is in flight.
3. Keep `docs/tech-debt.md` and this tracker in sync as Stage 4A advances toward the Stage 3B handoff.
4. Return to Stage 3B only after Stage 4A has made the Settings route legitimate enough to formalize.