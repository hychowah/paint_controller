# Paint Controller Modernization — Plan Documentation

> **Created**: 2026-04-16
> **Validated**: 2026-04-17 (post-implementation + test/documentation sync)
> **Branch**: `refactor`

## For Future LLM Sessions

> **Start at `INDEX.md` (repo root)** — it is the canonical session-start map for the whole repo. This file covers only the plan-documentation subset.

For plan-docs navigation, read in this order:

1. **`01_MASTER_PLAN.md`** — Authoritative task tracker, dependency graph, progress table, and next-task gate.
2. **`02_ARCHITECTURE.md`** — Current runtime architecture reference.
3. **`03_QML_BINDINGS.md`** — Current QML↔Python registration state and remaining import/qmldir cleanup scope.
4. **`04_AUDIT_REPORT.md`** — Historical pre-mortem rationale, not current status.

## Authority Hierarchy

- **Session-start navigator**: `docs/plan/00_README.md`
- **Authoritative progress and next-task source**: `docs/plan/01_MASTER_PLAN.md`
- **What was actually completed and validated**: `DEVNOTES.md`
- **Reusable technical gotchas and patterns**: `KNOWLEDGE.md`
- **Active task scratch only**: `PLANNING.md`
- **Historical context only**: `REFACTOR_TRACKER.md`, `docs/plan/04_AUDIT_REPORT.md`

If two files disagree, prefer the file higher in this list unless `DEVNOTES.md` documents a more recent verified result.

## Current Status Sources

- **Authoritative progress tracker**: `docs/plan/01_MASTER_PLAN.md`
- **Chronological completed work**: `DEVNOTES.md`
- **Active session scratch plan**: `PLANNING.md`
- **Operator/developer entry point**: `README.md`
- **Historical context only**: `REFACTOR_TRACKER.md`, `docs/plan/04_AUDIT_REPORT.md`

## Stale-File Warnings

- `PLANNING.md` is temporary scratch for the active task and should not be treated as the long-term source of truth.
- `REFACTOR_TRACKER.md` is archived context, not the active tracker.
- `04_AUDIT_REPORT.md` contains useful rationale, but some recommendations were superseded by the later context-property runtime strategy.
- Historical test-count or task-order claims in older notes can drift. Use the **Current Checkpoint** section in `01_MASTER_PLAN.md` as the active queue.

## Environment Note

- VS Code is pinned to the project interpreter in `.vscode/settings.json`: `python/paint_controller/venv/bin/python`
- The reliable local test command is `python/paint_controller/venv/bin/python -m pytest -q`
- The test inventory has moved well past the older `100 passed` snapshot. Revalidate any full-suite claim with a fresh local pytest run rather than trusting fixed counts in historical notes.
- `QT_QPA_PLATFORM` is force-assigned `"offscreen"` in `conftest.py` (overrides any shell-level `xcb` setting).
- If `PySide6` or `pytest` appear missing in-editor, check the selected interpreter first.

## Active Queue Snapshot

- Immediate priority: `3.5`, then `1.11a-e`, and finally `2.8`
- Deferred backlog: remaining Phase 2 theming work (`2.5b`, `2.5c`, `2.6a-c`, `2.7`) stays documented but is intentionally postponed until the hardening queue is complete

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
