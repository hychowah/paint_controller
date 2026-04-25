# Python Qt Architecture Debt Plan

> Created: 2026-04-25
> Reframed: 2026-04-25 after first-principles review
> Scope: Planning only. This document is a multi-session roadmap for making the Python `paint_controller` UI a more professional Qt/PySide6 application while preserving the working runtime, operator ergonomics, and safety boundaries already present in the repo.

## Executive Summary

The correct direction is still to keep the Python-first `paint_controller` runtime and professionalize the Qt boundary. That conclusion did not change. What changed is the understanding of where the architecture debt actually lives.

The earlier roadmap improved after preserving the overlay-first operating model, but it still gave too much priority to page cleanup, route taxonomy, and candidate model lists. That was not first-principles enough. For this product, a professional Qt architecture is not defined by having fewer pages, more pages, or more view models. It is defined by clear ownership.

The live architecture problems are these:

- QML still directly orchestrates some machine-affecting actions, persistence writes, and immediate side effects.
- `MainWindow.qml` still owns shell policy, screen placement, page construction, overlay composition, and backend signal handling.
- The product already behaves like a coordinated two-surface operator shell, but that is not yet treated as the architectural center of gravity.
- QML still reaches too many raw runtime objects through the broad context-property contract.
- The operator overlay is a real operating surface, but its lifecycle, role, and safety rules are still implicit.
- Settings authority is split between a strong Python settings core, a live operational overlay, and a partly placeholder settings page.
- Control selection and command execution are still coupled through the `OverlayController` / `ControlProcessor` relationship.
- The current workflow UI is not clearly long-term, so major workflow UI abstraction is risky until the behavior-tree direction is settled.

The plan now centers on five architecture goals:

1. One clear Python-owned boundary for machine-affecting application actions initiated from QML.
2. One clear authority for the coordinated two-surface shell and screen policy.
3. One clear authority for operational overlay state and ownership.
4. One clear authority for persisted settings and immediate-apply operator adjustments, classified by capability and operating-state legality.
5. A narrower, explicit QML contract that exposes operator-facing state instead of runtime internals.

That is the path toward a professional Qt program for this robot controller.

## How Future LLM Sessions Should Use This Plan

Every future implementation session must still follow `AGENTS.md`:

1. Read `INDEX.md`, `AGENTS.md`, `KNOWLEDGE.md`, this plan, and `docs/tech-debt.md`.
2. Read `docs/plan/00_ARCHITECTURE_PROGRESS.md` for the current stage/slice status.
3. Pick exactly one slice from this roadmap.
4. Create or update root `PLANNING.md` for that slice.
5. Ask: "Here is my plan in PLANNING.md. Ready to proceed?"
6. Implement only after explicit approval.
7. Validate with the tests listed for that slice.
8. Update `DEVNOTES.md` after meaningful debugging or implementation.
9. Update `docs/tech-debt.md` and `docs/plan/00_ARCHITECTURE_PROGRESS.md` when debt is discovered, split, resolved, or reprioritized.
10. Delete root `PLANNING.md` before merge if the repo workflow requires cleanup.

This document is a roadmap, not approval to modify code.

## What "Professional Qt" Means Here

For this repo, a professional Qt/PySide6 application should have these properties:

- QML is declarative, task-oriented, and mostly policy-free.
- Python owns hardware, ROS, safety, persistence, execution policy, and screen-role decisions that matter across surfaces.
- QML-facing objects are introduced to clarify ownership, not to wrap everything mechanically.
- The shell has one source of truth for navigation, screen role, and major surface visibility.
- Operational overlays are allowed to be first-class UI when the operator must preserve video or machine context during adjustments.
- Settings may appear in more than one surface if the surfaces serve different operator roles, but they must still come from one authority.
- Safety, actuator math, and emergency behavior never move into QML.
- The system is testable at the level of startup, shell behavior, screen policy, focused model logic, and safety-sensitive controller boundaries.

This is not a generic desktop CRUD app. A DJI-style operating surface can be a professional result here. The professionalism comes from explicit contracts and ownership, not from forcing everything into conventional pages.

## Root Reasons The UI Feels Over-Complicated

The repo is not over-complicated mainly because it has many files. The file count is not the core problem. The real causes are below.

### Root Reason A: QML-To-Application Action Boundaries Are Too Loose

Current evidence:

- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml` performs persisted updates and immediate hardware-side effects in the same QML interaction path.
- QML operational surfaces can directly trigger device, command, and workflow actions through raw runtime objects.
- The runtime context contract still exposes many internal objects directly to QML.

Why it matters:

- The highest-risk UI boundary is not only visual complexity; it is that QML can still orchestrate application behavior too directly.
- Rearranging pages or shells without first narrowing these action paths mostly moves symptoms around.
- A professional Qt program in this domain should let QML express user intent, while Python owns machine-facing application behavior.

### Root Reason B: Shell Authority Is Split

Current evidence:

- `python/paint_controller/qml/core/MainWindow.qml` owns root window configuration, screen selection, page component creation, overlay composition, and backend connections.
- `python/paint_controller/qml/navigation/SelectBar.qml` owns page-index routing and selected-button state.
- `python/paint_controller/services/screen_manager.py` exists, but screen policy is still partly computed in QML.

Why it matters:

- Shell behavior is hard to reason about because no single layer owns it.
- Navigation cleanup alone will not solve the problem if screen and overlay policy remain in the root QML file.
- Future sessions can easily change the wrong layer because the shell decision path is spread across QML and Python.

### Root Reason C: Operational Overlay Ownership Is Implicit

Current evidence:

- `python/paint_controller/qml/overlays/systemcontrol/SystemControlMenu.qml` contains device, command, settings, workflow, and editing surfaces.
- `python/paint_controller/qml/overlays/video/` is not just cosmetic overlay content; it is part of the main operating workflow.
- `MainWindow.qml` decides when the system-control overlay appears on the main window versus the secondary screen.

Why it matters:

- The operator overlay is a primary surface but is not documented as such in the architecture.
- Without an explicit contract, future cleanup work can accidentally weaken operator ergonomics.
- Overlay visibility and ownership are too easy to entangle with unrelated joystick or window logic.

### Root Reason D: QML Can Still See Too Many Runtime Internals

Current evidence:

- `python/paint_controller/core/app_runtime.py` registers a broad set of context properties directly into QML.
- Pages and overlays bind directly to controllers, services, handlers, recorders, and managers.

Why it matters:

- QML becomes structurally coupled to internal runtime construction.
- Python refactors have a wider blast radius than necessary.
- It is difficult to answer which UI surface truly owns which backend contract.

### Root Reason E: Settings Authority Is Split By Surface Instead Of Role

Current evidence:

- `python/paint_controller/core/settings.py` is the strong persistence and validation core.
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml` is the stronger live settings surface for real machine control.
- `python/paint_controller/qml/pages/settings/PageSettings.qml` still contains placeholder-like local values and should not be treated as authoritative.

Why it matters:

- The problem is not that two settings surfaces exist. The problem is that their authority relationship is unclear.
- Trying to collapse everything into one settings location too early would solve the wrong problem.
- A professional Qt architecture should support both operational quick-adjust surfaces and broader admin/setup surfaces when the workflow demands it.
- Capability class matters as much as surface role: some settings are live-adjustable, some require safe-stop, some are commissioning-only, and some are diagnostic-only.

### Root Reason F: Control Selection And Command Policy Are Still Cross-Coupled

Current evidence:

- `python/paint_controller/ui/overlay.py` still owns menu state and some selection logic.
- `python/paint_controller/handlers/control_processor.py` still consumes that selection state while also owning command math and dispatch.
- `controller_factory.py` documents the circular dependency.

Why it matters:

- Operator state and command execution are harder to change safely.
- The code path is harder to explain, test, and refactor.
- This is a more meaningful architecture target than feature reshuffling.

### Root Reason G: Automation Direction Is Not Settled

Current evidence:

- `python/paint_controller/services/workflow/workflow_runner.py` is already a Qt-facing runtime surface with timers and file watching.
- Workflow controls appear in multiple operational surfaces.
- A future behavior-tree runtime may replace the current workflow path.

Why it matters:

- Large workflow UI abstraction work can become throwaway architecture.
- The right near-term goal is transition-readiness and safety, not a grand workflow UI rebuild.

## Product Decisions And Non-Negotiable Invariants

These decisions are part of the architecture contract unless the user explicitly changes them later.

- Keep the Python-first runtime. Do not revive a second UI architecture path.
- Preserve the DJI-style overlay-first operating model.
- Treat the operator overlay as a first-class operating surface, not as an accidental anti-pattern.
- Keep multi-screen touchscreen ownership intact in dual-monitor mode.
- Use `setContextProperty()` rather than `qmlRegisterSingletonInstance()` in this repo.
- Keep migrations additive until the existing context-property contract is safely retired.
- Do not move safety, actuator math, or emergency behavior into QML.
- Do not invest heavily in the current workflow UI architecture until the behavior-tree direction is settled.

## Architectural Anti-Goals

This plan deliberately avoids these traps:

- Do not replace the broad context-property contract with one giant `Backend` object.
- Do not create six new facade objects just because facade objects sound architectural.
- Do not define success as “everything is a page.”
- Do not define success as “there is only one settings screen.”
- Do not start with large visual recomposition before ownership is clarified.
- Do not merge shell cleanup, overlay redesign, settings redesign, and control-model work into one session.

## Recommended Architecture Direction

The most defensible direction is:

1. Freeze the dangerous QML-to-application action boundary first.
2. Define the coordinated two-surface shell and screen ownership model second.
3. Break operator-selection state away from command execution third.
4. Formalize the operational overlay contract on top of those cleaner boundaries.
5. Clarify settings authority using both role and capability classes.
6. Stabilize workflow as a real current service, while keeping future behavior-tree language explicitly conditional.
7. Narrow the QML contract only after the correct owners are clearer.

This differs from the earlier version in two important ways: navigation cleanup is no longer near the front, and context-surface reduction is no longer treated as the first architecture tactic. Both are now consequences of cleaner ownership.

## Multi-Session Roadmap

The stages below are ordered by architecture value and risk reduction, not by visual neatness.

## Stage 0: Baseline Authority Map

Goal: build a durable map of who currently owns shell policy, overlay policy, settings policy, control-selection state, automation state, and machine-affecting application actions.

Complexity: Low
Risk: Low
Suggested sessions: 1

Primary files:

- Read-only: `python/paint_controller/core/app_runtime.py`
- Read-only: `python/paint_controller/qml/core/MainWindow.qml`
- Read-only: `python/paint_controller/qml/navigation/SelectBar.qml`
- Read-only: `python/paint_controller/qml/overlays/systemcontrol/`
- Read-only: `python/paint_controller/qml/overlays/video/`
- Read-only: `python/paint_controller/qml/pages/settings/`
- Read-only: `python/paint_controller/ui/overlay.py`
- Read-only: `python/paint_controller/handlers/control_processor.py`

Tasks:

1. Classify each significant UI surface as `shell`, `operational overlay`, `admin/setup surface`, `diagnostic surface`, or `transitional surface`.
2. For each surface, list which runtime objects it touches directly.
3. Identify where QML currently triggers machine-affecting commands, persistence writes, and immediate side effects.
4. Identify where screen policy is computed today.
5. Identify where overlay visibility and active-tab policy are computed today.
6. Classify settings surfaces as `authoritative`, `role-specific consumer`, `duplicate`, `placeholder`, or `transitional`.
7. Classify workflow surfaces as `transitional`, `long-term`, or `behavior-tree replacement candidate`.
8. Record the top five ownership ambiguities where more than one layer appears to decide the same thing.

Exit criteria:

- The repo has an explicit authority map.
- Overlay-first operating use cases are documented.
- QML-to-application action paths are identified before implementation.
- Settings and workflow surfaces are classified before any rewrite work starts.

Validation:

- Read-only stage; no tests required unless files are changed accidentally.

## Stage 1: Freeze QML-To-Application Action Boundaries

Goal: stop QML from directly orchestrating high-risk application behavior before broader shell or surface cleanup.

Complexity: High
Risk: High
Suggested sessions: 2 to 5

Primary files:

- `python/paint_controller/qml/overlays/systemcontrol/CommandTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`
- candidate Python-side application boundary files justified by the chosen slice
- `tests/test_settings_runtime.py`
- `tests/test_workflow_runner.py`
- relevant command/device/runtime tests for the touched slice

Current problem:

The live architectural risk is not only broad QML visibility. It is that some QML interactions still combine user intent, persistence, controller side effects, and runtime orchestration in one place.

Professional target:

- QML expresses user intent.
- Python owns the machine-affecting application boundary.
- Immediate-apply settings, command actions, device actions, and workflow actions are routed through Python-owned application interfaces rather than being directly orchestrated in QML.

Important design rule:

This stage is not a mechanical facade pass. It is a targeted freeze of the dangerous action boundary.

Implementation strategy:

1. Inventory the operational QML actions with the highest blast radius.
2. Introduce thin Python-owned action boundaries only for those paths.
3. Migrate one action family at a time: settings, commands, device control, or workflow.
4. Preserve visible behavior while reducing direct QML orchestration.

Exit criteria:

- The highest-risk QML action paths no longer directly combine persistence writes and hardware-side effects.
- The chosen action family has focused tests.
- Visible operator workflow remains unchanged.

Validation:

- relevant focused tests for the touched action family
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

Progress note:

- 2026-04-25: Stage 1A is complete for the manual-command family. `CommandTab.qml` now routes manual commands through a Python-owned `ManualCommandHandler` without changing the operator-facing command catalog. The next recommended Stage 1 slice is the immediate-apply settings outliers in `SettingsTab.qml`.

Risks:

- These paths are machine-facing and safety-sensitive.
- Over-generalizing the new action boundary would create unnecessary abstraction.

Rollback:

- Migrate one action family at a time.
- Keep old QML bindings until the Python-owned path is verified.

## Stage 2: Establish The Two-Surface Shell And Screen Authority

Goal: make shell policy professional by treating the product as a coordinated two-surface operator shell, not as a main window plus helper window.

Complexity: Medium
Risk: Medium to High
Suggested sessions: 2 to 4

Primary files:

- `python/paint_controller/qml/core/MainWindow.qml`
- `python/paint_controller/qml/overlays/MultiScreenListUI.qml`
- `python/paint_controller/services/screen_manager.py`
- `python/paint_controller/core/qt_bridge.py`
- `tests/test_startup_smoke.py`
- `tests/test_services_runtime.py`

Current problem:

The product already behaves as a coordinated external mission surface plus built-in touch-operated surface, but the architecture still describes and implements that behavior too implicitly.

Professional target:

- One place defines shell state and screen-role policy.
- One place defines secondary-window ownership as part of the product shell, not as an afterthought.
- Root QML becomes thinner and more declarative.
- QML can still bind to Qt screen objects where required, but it should not invent screen policy from scratch.

Implementation strategy:

1. Name the two product surfaces explicitly.
2. Move screen-role policy toward `ScreenManager` or a dedicated shell/screen adapter.
3. Reduce `MainWindow.qml` to composition and binding where practical.
4. Preserve dual-screen touch ownership as a first-class product requirement.

Exit criteria:

- The dual-surface shell is explicitly modeled.
- `MainWindow.qml` is no longer the place where raw screen count becomes product policy.
- Secondary-window behavior has focused tests.

Validation:

- `tests/test_startup_smoke.py`
- `tests/test_services_runtime.py`
- `tests/test_qml_imports.py`
- Manual multi-screen validation on hardware when available.

Risks:

- Qt screen timing is fragile.
- Multi-window behavior is hardware-specific.
- Offscreen tests cannot fully prove monitor placement.

Rollback:

- Add new shell/screen properties before removing old QML expressions.
- Preserve current monitor behavior until the new source of truth is verified.

## Stage 3: Break Control Selection Away From Command Execution

Goal: remove the `OverlayController` / `ControlProcessor` coupling before treating overlay architecture as stable.

Complexity: High
Risk: High
Suggested sessions: 3 to 6

Primary files:

- `python/paint_controller/ui/overlay.py`
- `python/paint_controller/handlers/input.py`
- `python/paint_controller/handlers/control_processor.py`
- `python/paint_controller/core/controller_factory.py`
- `python/paint_controller/core/state_store.py`
- `python/paint_controller/qml/overlays/JoystickOverlay.qml`
- `tests/test_input_handler.py`
- `tests/test_control_processor.py`
- `tests/test_safety_integration.py`

Current problem:

Selection state, overlay presentation, display state, and command policy are intertwined.

Professional target:

- A selection model owns operator selection state.
- Input handling turns hardware events into intent.
- Control processing owns command math and hardware dispatch.
- Overlay presentation reads declarative state instead of shaping command policy indirectly.

Important design rule:

This is one of the few areas where a dedicated Qt-facing model is strongly justified because it separates UI selection state from machine command policy.

Exit criteria:

- The circular dependency note disappears from `controller_factory.py`.
- Selection state is explainable without reading command-dispatch code.
- Safety-sensitive command behavior remains covered by tests.

Validation:

- `tests/test_input_handler.py`
- `tests/test_control_processor.py`
- `tests/test_safety_integration.py`
- `tests/test_startup_smoke.py`

Risks:

- Operator muscle memory depends on current control behavior.
- Small state-model mistakes can create safety regressions.

Rollback:

- Preserve old adapter methods during migration.
- Move one caller at a time.

## Stage 4: Formalize The Operational Overlay Contract

Goal: turn the overlay-first operating model into explicit architecture after the action boundary and selection-state boundary are cleaner.

Complexity: High
Risk: High
Suggested sessions: 2 to 5

Primary files:

- `python/paint_controller/qml/overlays/systemcontrol/SystemControlMenu.qml`
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/CommandTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`
- `python/paint_controller/qml/overlays/video/`
- `python/paint_controller/qml/core/MainWindow.qml`
- `python/paint_controller/ui/overlay.py`
- `python/paint_controller/handlers/input.py`

Current problem:

The operator overlay is real product architecture, but its rules are implicit. The project benefits from it ergonomically while still carrying it as architecture debt.

Professional target:

Define the overlay contract explicitly:

- which surfaces are operational overlays versus modal overlays versus maintenance/setup surfaces
- which actions are allowed during active operation
- which settings are safe quick-adjust settings
- which actions require confirmation, safe-stop, or maintenance mode
- which screen owns the touch-oriented overlay in single-screen and dual-screen modes
- how overlay visibility interacts with joystick menus, emergency UI, and fullscreen video

Important design rule:

Do not treat overlays as second-class just because they are overlays. For this product, an overlay can be the correct primary surface.

Implementation strategy:

1. Classify all system-control tabs and video subpanels by role and safety class.
2. Keep operational tabs overlay-first.
3. Move only non-operational maintenance/setup concerns out of the overlay when doing so improves clarity.
4. Separate overlay visibility policy from unrelated command-selection state.
5. Introduce an overlay model only if it clarifies ownership instead of becoming another catch-all object.

Exit criteria:

- The overlay-first operating workflow is documented and protected.
- Operational settings and commands have a clear overlay home.
- Maintenance and setup concerns have a clear home and clearer legality rules.
- Overlay state is not accidentally defined by unrelated command logic.

Validation:

- `tests/test_input_handler.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- services runtime tests if screen behavior changes
- workflow tests only if workflow tabs are touched

Risks:

- Steam Deck inputs assume quick overlay access.
- Dual-screen touch ownership is part of operator ergonomics.
- Over-cleaning the overlay would regress the product even if the code looks cleaner.

Rollback:

- Keep existing overlay entry points during transition.
- Introduce any maintenance/setup alternative alongside the overlay, not instead of it, until validated.

## Stage 5: Bounded Navigation Registry Cleanup

Goal: remove fragile page-index routing once the shell is better defined.

Complexity: Medium
Risk: Medium
Suggested sessions: 1 to 3

Primary files:

- `python/paint_controller/qml/core/MainWindow.qml`
- `python/paint_controller/qml/navigation/SelectBar.qml`
- optional new QML registry file if justified
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

Current problem:

`SelectBar.qml` still maps page indexes to components via switch logic, while `MainWindow.qml` defines those components and transition rules separately.

Professional target:

- One route registry exists.
- Route identity is explicit.
- Button rendering consumes the route registry rather than duplicating it.
- Indexes may remain as compatibility metadata during transition, but they stop being the real architecture.

Why this stays bounded:

Navigation cleanup is worthwhile, but it is still a shell consequence, not the core product-architecture problem.

Exit criteria:

- No hard-coded page switch statement remains.
- Adding a route requires one source-of-truth edit.
- Compatibility with current transitions and button selection is preserved.

Validation:

- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- add route-navigation smoke coverage if the shell test surface is widened

Risks:

- StackView direction logic still depends on relative order.
- Steam Deck navigation may still assume index-compatible behavior.

Rollback:

- Keep legacy route order metadata until all callers are migrated.

## Stage 6: Define Settings Authority, Capability Classes, And Role-Based Surfaces

Goal: make settings architecture professional by clarifying authority, role, and operating-state legality.

Complexity: Medium
Risk: Medium
Suggested sessions: 2 to 4

Primary files:

- `python/paint_controller/core/settings.py`
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`
- `python/paint_controller/qml/pages/settings/PageSettings.qml`
- `python/paint_controller/qml/pages/settings/components/`
- `python/paint_controller/qml/pages/settings/pages/`
- `python/paint_controller/qml/pages/tuning/PageTuning.qml`
- `tests/test_settings_runtime.py`

Current problem:

The repo already has a good settings authority on the Python side. The UI problem is that settings surfaces do not yet have a clear relationship by role and capability.

Professional target:

- One authority for persisted values and validation.
- One explicit distinction between quick operational adjustments and broader maintenance/setup surfaces.
- Clear capability classes such as `live-adjustable`, `safe-stop-required`, `commissioning-only`, and `diagnostic-only`.
- No placeholder settings surface pretending to be authoritative.
- No duplicated local QML state where Python authority already exists.

Design rule:

The goal is not “one settings page.” The goal is “one settings authority with intentional operator/admin presentations and explicit legality rules.”

Implementation strategy:

1. Classify each setting as `persisted only`, `persisted + immediate apply`, `runtime-only`, or `deprecated`.
2. Classify each setting by capability and operating-state legality.
3. Identify which settings belong in the operator overlay because they are genuinely in-operation adjustments.
4. Identify which settings belong in maintenance/setup surfaces.
5. Remove placeholder local state from `PageSettings.qml` before treating it as part of the real architecture.
6. Introduce grouped metadata or a settings adapter only if it simplifies the UI contract meaningfully.

Exit criteria:

- Each setting has one authority.
- Multiple surfaces may exist, but their roles and legality rules are explicit.
- Placeholder local settings state is removed or clearly marked transitional.
- Atomic persistence and validation remain intact.

Validation:

- `tests/test_settings_runtime.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

Risks:

- Operational settings may need immediate machine side effects.
- Users may rely on current overlay placement for quick adjustment.

Rollback:

- Keep the operational overlay settings path working while maintenance/setup surfaces are stabilized.

## Stage 7: Workflow Stabilization And Conditional Behavior-Tree Readiness

Goal: keep the current workflow path safe and maintainable as a real current service while keeping future behavior-tree language explicitly conditional.

Complexity: Medium
Risk: Medium
Suggested sessions: 2 to 4

Primary files:

- `python/paint_controller/services/workflow/workflow_runner.py`
- `python/paint_controller/services/workflow/workflow_executor.py`
- `python/paint_controller/services/workflow/scheduler.py`
- `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`
- `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml`
- `tests/test_workflow_runner.py`
- `tests/test_workflow_executor.py`
- `tests/test_workflow_scheduler.py`

Current problem:

The workflow runtime already exposes a Qt-facing interface and should be stabilized where necessary, but the long-term automation direction may change substantially.

Professional target:

- Safe start/stop/recover behavior.
- Less repeated QML polling and less fragile persistence.
- Clear identification of transitional workflow UI pieces.
- Explicit seams for a future behavior-tree runtime, but only as future-oriented seams rather than assumed replacement.

Design rule:

Prefer tightening `WorkFlowRunner` in place over inventing a large second abstraction layer.

Exit criteria:

- Workflow UI is safe and maintainable for the transition period.
- Current workflow investment is proportional to its expected lifetime.
- Behavior-tree migration seams are identified without pretending the replacement is already decided.

Validation:

- `tests/test_workflow_runner.py`
- `tests/test_workflow_executor.py`
- `tests/test_workflow_scheduler.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

Risks:

- Workflow execution is actuator-facing.
- Editor and runtime concerns can drift together.

Rollback:

- Keep the existing `workFlowRunner` contract while making internal hardening improvements.

## Stage 8: Narrow The QML Contract After Owners Are Clear

Goal: reduce raw context-property exposure only after action boundaries, shell ownership, overlay ownership, settings authority, and control ownership are better defined.

Complexity: Medium
Risk: Medium
Suggested sessions: 2 to 5

Primary files:

- `python/paint_controller/core/app_runtime.py`
- candidate new adapter/model files only where justified
- tests around runtime registration and any new model logic

Current problem:

The repo has too many QML-visible runtime objects, but the earlier plan risked solving that with a broad facade taxonomy before the right ownership boundaries were known.

Professional target:

- Introduce QML-facing adapters only where they reduce real cross-cutting coupling.
- Reduce direct controller/service exposure where pages or overlays should depend on an operator-facing contract instead.
- Treat context-property reduction as an outcome of better architecture, not as the opening move.

Good candidates after earlier stages succeed:

- a shell/navigation model if shell ownership is stabilized
- a control-selection model as part of Stage 3
- a settings adapter only if it meaningfully clarifies grouped metadata, capability classes, and legality rules
- a screen/shell adapter only if it becomes the cleanest owner of the dual-surface shell

Bad candidates:

- wrappers added only to reduce a number in a metric
- large “everything UI needs” objects
- a workflow facade built before the automation direction is settled

Exit criteria:

- Fewer raw runtime internals are directly referenced by QML.
- New adapters have crisp ownership and focused tests.
- The context-property count goes down because architecture improved, not because everything was hidden behind one umbrella object.

Validation:

- `tests/test_controller_factory_runtime.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- focused tests for any new adapter/model

Risks:

- Mechanical wrapping can create indirection without reducing coupling.

Rollback:

- Keep old context properties while new contracts are proven.

## Stage 9: Optional Feature-Shell Recomposition

Goal: reorganize visible destinations only if earlier ownership work shows a real product benefit.

Complexity: High
Risk: High
Suggested sessions: optional, many small slices

Status in this roadmap:

This is explicitly optional and downstream. It is not the main architecture lane.

Why:

Feature-shell recomposition is product design work enabled by architecture improvements, not architecture debt paydown by itself.

Use this stage only when:

- the action boundary is safer
- the dual-surface shell is stable
- overlay ownership is explicit
- settings authority is clear
- route registry is already maintainable

Possible outcomes:

- fewer top-level destinations
- clearer separation between operation, maintenance/setup, diagnostics, and automation
- better alignment between route names and operator language

Important:

Do not use this stage to force common in-operation work out of the overlay.

Validation:

- startup smoke
- QML import smoke
- affected focused tests
- manual operator-task trace on real hardware when possible

Rollback:

- keep legacy destinations available until new flows are validated

## Stage 10: Design-System And Styling Cleanup

Goal: finish visual consistency after architecture is stable.

Complexity: Low to Medium
Risk: Low
Suggested sessions: as needed

Primary files:

- `python/paint_controller/qml/core/CommonStyle.qml`
- `python/paint_controller/qml/overlays/video/components/VideoOverlayStyle.qml`
- remaining hardcoded colors and spacing in pages and overlays
- `docs/tech-debt.md` items TD-002 and TD-016

Professional target:

- one theme source or clearly layered theme extensions
- good 7-inch readability
- touch-sized targets
- no layout anti-patterns inside `RowLayout` / `ColumnLayout`

Validation:

- `tests/test_qml_imports.py`
- `tests/test_startup_smoke.py`
- `qmllint` if available
- manual visual pass on target display when possible

## Suggested Session Order

Use this order unless a production bug interrupts it:

1. Stage 0 authority map.
2. Stage 1 QML-to-application action boundary freeze.
3. Stage 2 two-surface shell and screen authority.
4. Stage 3 control-selection boundary.
5. Stage 4 operational overlay contract.
6. Stage 5 bounded navigation registry cleanup.
7. Stage 6 settings authority, capability classes, and role-based surfaces.
8. Stage 7 workflow stabilization and conditional behavior-tree readiness.
9. Stage 8 narrower QML contract where justified.
10. Stage 9 optional feature-shell recomposition.
11. Stage 10 design-system cleanup.

Why this order changed:

The earlier order still attacked the shell and route symptoms before the highest-risk application boundary. The new order first freezes dangerous QML-to-application action paths, then models the product shell as a coordinated two-surface system, then untangles control state before overlay formalization. Route cleanup and context-surface reduction remain important, but they are now explicitly downstream consequences.

## Technical Guardrails

- Never use `qmlRegisterSingletonInstance()` in this repo.
- Do not move safety logic or actuator command math into QML.
- Do not let new QML surfaces directly combine persistence writes, controller side effects, and operator intent handling in one place.
- Do not replace 22 context properties with one giant `Backend` object.
- Do not remove the overlay-first operating workflow unless the user explicitly changes product direction.
- Do not treat all overlays as transient by default.
- Do not treat the built-in touchscreen window as an auxiliary surface; it is part of the product shell.
- Do not treat “one settings location” as the architecture goal.
- Do not invest heavily in current workflow UI abstraction until the behavior-tree direction is settled.
- Keep migrations additive while old QML consumers still exist.
- Keep `AppRuntime` as the composition root, not as a behavior god object.
- Keep cleanup order explicit and validated.
- After shell or screen changes, run startup and services validation.
- After overlay or input changes, run input and smoke validation.
- After control-state changes, run control processor and safety validation.
- After workflow changes, run workflow validation.
- After settings changes, run settings runtime validation.

## Success Metrics

Track these across sessions:

- Number of machine-affecting actions initiated directly from QML.
- Number of shell decisions computed in `MainWindow.qml` versus owned elsewhere.
- Number of places where raw screen count or raw `Qt.application.screens` data becomes product policy.
- Whether the two-surface shell has explicit named ownership.
- Number of operational overlays with explicit ownership and lifecycle rules.
- Number of settings surfaces classified by role, capability class, and authority.
- Number of placeholder local settings values remaining in QML.
- Number of raw controller/service objects directly referenced by each major surface.
- Whether the overlay/control circular dependency still exists.
- Whether workflow UI is explicitly treated as transitional or long-term.
- Startup smoke status.
- QML import smoke status.
- Relevant focused test status.

Secondary metrics, not primary goals:

- context-property count
- number of top-level routes
- files touched to add a route

Suggested target after major refactor:

- High-risk QML action paths route through Python-owned application boundaries.
- Shell and screen policy have one obvious owner.
- The two-surface operator shell is explicit in the architecture.
- The operator overlay is explicitly part of the architecture, not accidental inherited behavior.
- Settings authority is singular even if role-specific surfaces remain plural.
- Control selection no longer shares an ownership cycle with command execution.
- Workflow remains safe and maintainable without overcommitting to a possibly transitional UI architecture.
- QML consumes fewer runtime internals because the right owners became clear.

## Plan Maintenance

When a stage is completed:

1. Add a short completion note here or in `docs/tech-debt.md`.
2. Move any resolved debt in `docs/tech-debt.md` to the resolved table.
3. Add a `DEVNOTES.md` entry if meaningful debugging occurred.
4. Update `docs/plan/00_ARCHITECTURE_PROGRESS.md` so the current stage/slice status stays truthful.
5. If a reusable gotcha is discovered, ask the user before adding it to `KNOWLEDGE.md`.

When a stage becomes wrong:

1. Do not keep following it mechanically.
2. Update this document with the new decision and reason.
3. Prefer a targeted correction over another full rewrite unless the architecture direction truly changed.

## Next Recommended Session

Stage 1A is now complete for the manual-command family. The next recommended session is Stage 1B preparation and implementation planning for the immediate-apply settings outliers.

Task title: Formalize the Stage 0 authority map artifact and plan the Stage 1B settings-outlier boundary freeze.

The session should:

1. Reconfirm the current owners of shell, screen, overlay, settings, control-selection, and machine-affecting application actions against the merged Stage 1A code.
2. Decide whether the Stage 0 authority map should be merged as its own durable artifact before more implementation slices land.
3. Identify the exact `SettingsTab.qml` paths where QML still combines UI parsing, persistence writes, and immediate side effects.
4. Keep the Stage 1B slice narrow to the immediate-apply settings outliers rather than broadening into all settings UI.
5. Create `PLANNING.md`.
6. Ask for confirmation.

The likely next implementation slice after approval:

- move the immediate-apply settings outliers behind Python-owned methods without changing operator behavior
- preserve dual-screen behavior
- preserve overlay-first operation
- validate startup, imports, and the relevant focused settings/runtime tests for the migrated action family