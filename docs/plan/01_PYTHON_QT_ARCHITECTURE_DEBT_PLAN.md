# Python Qt Architecture Debt Plan

> Created: 2026-04-25
> Rewritten: 2026-04-28
> Scope: Durable architecture guidance only. This document explains the architecture target, invariants, anti-goals, and historical completion context. It is not the live execution tracker.

## Purpose

The point of this refactor is not cosmetic cleanup. It is to make the application easier to maintain, easier to scale, and easier for humans to reason about.

For this repo, that means:

- fewer equal-owner paths for one operator-visible behavior
- smaller blast radius when runtime internals change
- narrower app-scope QML exposure
- clearer separation between QML presentation and Python-owned policy, persistence, safety, and machine behavior
- validation that follows real ownership boundaries instead of accidental ambient access

The application should feel more like a professional Qt program because QML composes and presents while Python owns cross-surface state, policy, and machine-affecting behavior.

## North Star

- Each operator-visible behavior should have one canonical Python owner and one declarative QML consumer.
- No checkpoint is complete until the old read path it supersedes is retired or explicitly quarantined.
- Success is measured by smaller permanent QML surface area and fewer durable architecture concepts, not by namespacing alone.
- Any new contract must survive beyond one slice and remove a raw app-scope QML dependency in the same family.

## Durable Architecture Goals

1. One clear Python-owned boundary for machine-affecting actions initiated from QML.
2. One clear authority for shell policy, route identity, and fullscreen host behavior.
3. One clear authority for overlay host placement, overlay legality, and operator-facing overlay state.
4. One truthful settings architecture with one Python authority and explicit operator versus admin semantics.
5. One stable workflow path for the live system, with future automation migration kept separate from present-system stabilization.
6. A narrower, explicit QML contract that exposes operator-facing state instead of runtime internals.

## Non-Negotiable Invariants

- Keep the Python-first runtime. Do not reintroduce a second UI architecture path.
- Preserve the overlay-first operating model.
- Treat the operator overlay as a first-class operating surface.
- Keep the top-level Settings route as a real long-term admin or maintenance surface.
- In dual-monitor mode, keep the built-in Steam Deck display as the touch/control surface and the external monitor as the mission surface.
- Keep behavior-tree migration as a future direction, but do not let it destabilize the current workflow system.
- Use `setContextProperty()` rather than `qmlRegisterSingletonInstance()` in this repo.
- Do not move safety, actuator math, or emergency behavior into QML.
- Keep `AppRuntime` as the composition root.

## Anti-Goals

- Do not replace the current context-property bag with one giant `Backend` object.
- Do not build a broad `OperatorSession` or similar mega-session abstraction.
- Do not create facade objects that only rename the same ambient access.
- Do not define success as flattening everything into pages.
- Do not define success as collapsing all settings into one visual location.
- Do not merge shell cleanup, telemetry cleanup, settings cleanup, and workflow redesign into one implementation slice.

## What Professional Qt Means Here

- QML stays declarative, task-oriented, and light on policy.
- Python owns hardware, ROS, safety, persistence, workflow execution, and screen-role decisions that matter across surfaces.
- QML-facing contracts are introduced to clarify ownership, not to mechanically wrap everything.
- Feature roots and bounded models should shrink the app-scope QML contract rather than duplicate it.
- Operational overlays are valid primary UI in this product because the operator must preserve machine and video context during adjustments.
- Settings may appear in more than one surface when operator roles differ, but all truthful settings still come from one authority.

## Why The UI Felt Over-Complicated

The historic complexity came from ownership ambiguity more than from raw file count.

### QML saw too much runtime internals

The broad app-scope context-property surface made QML structurally dependent on runtime construction details.

### Shell authority was split

Route identity, screen policy, and host composition were spread across QML and Python seams that were not cleanly documented.

### Overlay ownership was implicit

The overlay-first workflow was product architecture, but the code and docs did not state that clearly enough.

### Settings truth and legality had drifted apart

The repo needed truthful settings data and a clearer legality seam instead of another round of visual reshuffling.

### Workflow debt had two horizons

The current workflow system needed hardening for today, while future automation migration needed separate seams rather than speculative rewrites.

## Current Architecture Position

The repo has already completed the high-risk ownership work for these families:

- Stage 1 command, device, and workflow boundary freezes
- Stage 2 overlay and control-selection ownership freeze
- Stage 3 shell policy and route normalization
- Stage 4 truthful settings and capability inventory
- Stage 4.5 direct-admin boundary and default-gating work
- Workstream A workflow runtime and editor stabilization
- Workstream B overlay host and legality work
- Workstream C shell and route formalization
- Workstream D QML contract reduction for the settings family and unused context exposure

The unfinished tail is no longer a generic cleanup program. It is a bounded boundary-retirement program focused on remaining raw-global telemetry families.

The live execution order is intentionally delegated to [docs/plan/00_ARCHITECTURE_PROGRESS.md](/home/c3spray_deck/ros2_ws/src/paint_controller_ros2/docs/plan/00_ARCHITECTURE_PROGRESS.md) so this file stays durable instead of becoming a second live tracker.

## Execution Model

Completed stages and workstreams remain useful historical record, but live implementation work now follows a simpler rule set:

- one live control board
- one active family at a time unless two adjacent families are intentionally coupled
- one canonical owner per touched behavior
- one explicit retirement or quarantine decision for the old read path
- one focused validation band that matches the touched ownership boundary

## Historical Completion Summary

### Stage 0

- Published the initial authority map so future work could reason about ownership instead of only file structure.

### Stage 1

- Moved command, device, and workflow action families off direct QML orchestration and behind Python-owned boundaries.

### Stage 2

- Removed the live `OverlayController` and `ControlProcessor` cycle, extracted `JoystickSelectionModel`, and stabilized overlay and selection ownership.

### Stage 3

- Split shell policy into bounded Python ownership and made route identity key-first and canonical.

### Stage 4

- Made the Settings route truthful for schema-backed settings, kept camera explicit summary-only, and introduced `CapabilityCatalog`.

### Stage 4.5

- Removed the remaining tracked direct admin and calibration mutators from QML and made default gating explicit in Python.

### Workstream A

- Stabilized workflow runtime and editor behavior around one Python-owned runtime contract.

### Workstream B

- Made overlay host placement and legality explicit and shared.

### Workstream C

- Finished shell and route formalization for the touched shell family.

### Workstream D

- Reduced the settings-family contract surface and retired unused root-context exposure.

### Workstream E So Far

- Retired workflow/editor and command globals behind `systemControlServices`.
- Partially retired fullscreen video roots behind bounded `videoRuntime`.
- Retired shared winch, teensy, wheel, and recording seams behind bounded status contracts.
- Retired the tracked shell/home/launcher telemetry and Launcher admin seams behind `shellConnectivityStatus` and `launcherAdmin`.
- Retired the page-level wheel detail seam and the page/shared-card winch detail seam behind existing `wheelStatus` and `winchStatus`.
- Retired the shared teensy/end-effector detail telemetry seam behind extended `teensyStatus` plus bounded `valveStatus`.
- Retired the monitor and wall-detection lidar seam behind bounded `lidarStatus`.
- Retired the remaining fullscreen overlay wheel and winch telemetry reads behind existing `wheelStatus` and `winchStatus`.
- Retired the remaining `PageHome.qml` preview and frame-refresh remainder behind explicit `videoRuntime` ownership while the cleanup wave split the supporting startup-smoke and runtime guard surfaces into smaller, local files.

## Guidance For Future Sessions

Future implementation sessions should:

1. Read `INDEX.md` and `AGENTS.md` first.
2. Check `KNOWLEDGE.md` before debugging.
3. Read `DEVNOTES.md` for the latest verified runtime state.
4. Read [docs/plan/00_ARCHITECTURE_PROGRESS.md](/home/c3spray_deck/ros2_ws/src/paint_controller_ros2/docs/plan/00_ARCHITECTURE_PROGRESS.md) for the only live execution order.
5. Use this document for durable rationale and historical completion context.
6. Read `docs/tech-debt.md` before starting a new family.
7. Pick one bounded family slice.
8. Update `PLANNING.md` before editing.
9. Validate against the touched ownership boundary.
10. Update `DEVNOTES.md` and `docs/tech-debt.md` after meaningful work.

This document should not carry slice-by-slice live sequencing again.