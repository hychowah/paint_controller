# Paint Controller Modernization — Plan Documentation

> **Created**: 2026-04-16
> **Validated**: 2026-04-22 (post-implementation + test/documentation sync)
> **Branch**: `refactor`

## For Future LLM Sessions

> **Start at `INDEX.md` (repo root)** — it is the canonical session-start map for the whole repo. This file covers only the plan-documentation subset.

This branch is **refactor-first**. The intent is to improve architecture, safety, shutdown/threading behavior, typing coverage, and defensive QML correctness before resuming feature delivery. If you are unsure whether to add a feature or reduce debt, choose the debt/hardening path unless the user explicitly reprioritizes.

For plan-docs navigation, read in this order:

1. **`01_MASTER_PLAN.md`** — Authoritative task tracker, dependency graph, progress table, and next-task gate.
2. **`02_ARCHITECTURE.md`** — Current runtime architecture reference.
3. **`03_QML_BINDINGS.md`** — Current QML↔Python registration state and remaining import/qmldir cleanup scope.

## Authority Hierarchy

- **This file is a plan-doc navigator only**; repo-wide authority starts at `INDEX.md`
- **Authoritative progress and next-task source**: `docs/plan/01_MASTER_PLAN.md`
- **What was actually completed and validated**: `DEVNOTES.md`
- **Reusable technical gotchas and patterns**: `KNOWLEDGE.md`
- **Active task scratch only**: `PLANNING.md`
- **Historical context only**: older DEVNOTES references to removed tracker/audit docs

If two files disagree, prefer `INDEX.md`'s repo-wide authority hierarchy first. Within the plan-doc subset, prefer the file higher in this list unless `DEVNOTES.md` documents a more recent verified result.

## Current Status Sources

- **Authoritative progress tracker**: `docs/plan/01_MASTER_PLAN.md`
- **Chronological completed work**: `DEVNOTES.md`
- **Active session scratch plan**: `PLANNING.md`
- **Operator/developer entry point**: `README.md`
- **Historical context only**: older DEVNOTES references to removed tracker/audit docs

## Stale-File Warnings

- `PLANNING.md` is temporary scratch for the active task. If it exists, verify the task title/date still match the currently approved work before trusting it.
- Historical notes may still mention the removed audit report; treat those references as background only and rely on `01_MASTER_PLAN.md` + `02_ARCHITECTURE.md` for current direction.
- Historical test-count or task-order claims in older notes can drift. Use the **Current Checkpoint** section in `01_MASTER_PLAN.md` as the active queue.

## Avoid / Defer

- Do not start net-new feature work unless the user explicitly reprioritizes it over refactoring.
- **`TD-001` Stage 1 is complete**: QML structural flatten, constructor-surface hardening, offscreen smoke coverage, and warn-only `qmllint` CI are all in place.
- **`TD-031` is complete**: the page-registry cleanup, overlay-hosted `systemcontrol` extraction, video feature-boundary extraction, and `CommonStyle` relocation are landed. The next work is the low-priority backlog, not another blocking structural stage.
- URI-module migration, broad lidar/pointcloud restructuring, and any optional root-file rename remain deferred to a later dedicated stage.
- Keep using `setContextProperty()`; do not re-open singleton-registration work with `qmlRegisterSingletonInstance()`.
- Treat `PLANNING.md` as session scratch only. If it conflicts with `DEVNOTES.md` or `01_MASTER_PLAN.md`, it loses.

## Environment Note

- Use the project interpreter `python/paint_controller/venv/bin/python` for editor tooling and tests
- The reliable local test command is `python/paint_controller/venv/bin/python -m pytest -q`
- Latest verified local full-suite result is `170 passed` on 2026-04-24.
- The test inventory has moved well past the older `100 passed` snapshot. Revalidate any full-suite claim with a fresh local pytest run rather than trusting fixed counts in historical notes.
- `QT_QPA_PLATFORM` is force-assigned `"offscreen"` in `conftest.py` (overrides any shell-level `xcb` setting).
- If `PySide6` or `pytest` appear missing in-editor, check the selected interpreter first.

## Active Queue Snapshot

- Just completed: `3.10 Static typing gate expansion`, `2.8 Fix page naming`, `TD-030 runtime/workflow/service validation hardening`, `TD-001 Stage 1 QML structural flatten + hardening + validation gates`
- Just completed: `TD-031` narrowed structural rebuild (page registry, overlay-hosted `systemcontrol`, video feature boundary, `CommonStyle` relocation)
- Non-blocking backlog after `TD-031`: `2.5b`, `2.5c`, `2.6a-c`, `2.7`, `TD-016`

## Branch Exit Bar

The refactor branch is considered done enough to resume feature work when:
- No medium/high-priority debt remains open in `docs/tech-debt.md`
- Full pytest is green
- Pyright is green for the covered scope
- ROS build is green
- Offscreen startup/shutdown smoke is green
- No known unresolved shutdown, thread-affinity, or safety-path defect remains active

## Key Paths

- **Python app**: `python/paint_controller/`
- **QML UI**: `python/paint_controller/qml/`
- **Launch files**: `launch/`
- **Tests**: `tests/`
- **Config**: `python/config/`

## Build & Run

```bash
cd ~/ros2_ws && colcon build --packages-select paint_interfaces paint_controller_ros2
paint_controller
```

## Validate

```bash
python/paint_controller/venv/bin/python -m pytest -q
```

## Rules

- Follow `copilot-instructions.md` workflow (Plan → Confirm → Implement → Cleanup)
- Update `PLANNING.md` (repo root) for active task
- Update progress tracker in `01_MASTER_PLAN.md` after each task
- Update `DEVNOTES.md` after significant debugging
- Prefer expanding this file over creating a second LLM index file; duplicate indexes will drift
