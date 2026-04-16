# Paint Controller Modernization — Plan Documentation

> **Created**: 2026-04-16
> **Validated**: 2026-04-16 (post-audit)
> **Branch**: `refactor`

## For Future LLM Sessions

Read files in this order:

1. **`01_MASTER_PLAN.md`** — The validated task list, dependency graph, progress tracker. Start here.
2. **`02_ARCHITECTURE.md`** — Full system architecture reference (layers, threading, data flows).
3. **`03_QML_BINDINGS.md`** — QML↔Python binding inventory, context properties, signal connections.
4. **`04_AUDIT_REPORT.md`** — Pre-mortem audit findings, verdicts, and dismissed concerns.
5. **`KNOWLEDGE.md`** (repo root) — Qt/Python gotchas and reusable patterns.
6. **`DEVNOTES.md`** (repo root) — Historical debugging notes.

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

## Rules

- Follow `copilot-instructions.md` workflow (Plan → Confirm → Implement → Cleanup)
- Update `PLANNING.md` (repo root) for active task
- Update progress tracker in `01_MASTER_PLAN.md` after each task
- Update `DEVNOTES.md` after significant debugging
