# Paint Controller Modernization — Plan Documentation

> **Created**: 2026-04-16
> **Validated**: 2026-04-17 (post-implementation + test/documentation sync)
> **Branch**: `refactor`

## For Future LLM Sessions

Read files in this order:

1. **`01_MASTER_PLAN.md`** — Authoritative task tracker, dependency graph, progress table, and next-task gate. Start here.
2. **`DEVNOTES.md`** (repo root) — Most recent completed work, validation results, and environment notes.
3. **`KNOWLEDGE.md`** (repo root) — Qt/Python gotchas and reusable patterns.
4. **`02_ARCHITECTURE.md`** — Current runtime architecture reference.
5. **`03_QML_BINDINGS.md`** — Current QML↔Python registration state and remaining migration scope.
6. **`04_AUDIT_REPORT.md`** — Historical pre-mortem rationale, not current status.
7. **`REFACTOR_TRACKER.md`** (repo root) — Optional historical context only; not the active tracker.

## Current Status Sources

- **Authoritative progress tracker**: `docs/plan/01_MASTER_PLAN.md`
- **Chronological completed work**: `DEVNOTES.md`
- **Active session scratch plan**: `PLANNING.md`
- **Operator/developer entry point**: `README.md`
- **Historical context only**: `REFACTOR_TRACKER.md`, `docs/plan/04_AUDIT_REPORT.md`

## Environment Note

- VS Code is pinned to the project interpreter in `.vscode/settings.json`: `python/paint_controller/venv/bin/python`
- The reliable local test command is `python/paint_controller/venv/bin/python -m pytest -q`
- If `PySide6` or `pytest` appear missing in-editor, check the selected interpreter first.

## Key Paths

- **Python app**: `python/paint_controller/`
- **QML UI**: `python/paint_controller/qml/`
- **C++ node** (deprecated): `src/`
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
