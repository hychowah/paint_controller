# Architecture Progress

Status board for the active architecture roadmap in `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`.

Use this file for current stage status and next-slice tracking.
Use `DEVNOTES.md` for verified implementation history.
Use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for the architecture rationale and staged roadmap.

## Current State

- Overall status: in progress
- Last completed slice: Stage 1A manual command boundary freeze
- Next recommended slice: Stage 1B immediate-apply settings outlier freeze
- Linux validation status: complete after rebasing onto `refactor`
- Last focused validation: `20 passed` for `tests/test_manual_command_handler.py`, `tests/test_controller_factory_runtime.py`, and `tests/test_startup_smoke.py`
- Latest full validation: `179 passed` for `python/paint_controller/venv/bin/python -m pytest -q`

## Stage Board

| Stage | Status | Notes |
|---|---|---|
| Stage 0 | in progress | Discovery pass completed in-session; durable authority-map artifact still not merged as a standalone repo doc |
| Stage 1 | in progress | Stage 1A complete; Stage 1B settings outliers still pending |
| Stage 2 | not started | Two-surface shell and screen authority |
| Stage 3 | not started | Control-selection state vs command execution decoupling |
| Stage 4 | not started | Operational overlay contract |
| Stage 5 | not started | Bounded navigation registry cleanup |
| Stage 6 | not started | Settings authority, capability classes, role-based surfaces |
| Stage 7 | not started | Workflow stabilization and conditional behavior-tree readiness |
| Stage 8 | not started | Narrower QML contract after owners are clear |
| Stage 9 | not started | Optional feature-shell recomposition |
| Stage 10 | not started | Design-system cleanup |

## Completed Slices

### 2026-04-25 - Stage 1A Manual Command Boundary Freeze

- Added Python-owned `ManualCommandHandler` and rewired `CommandTab.qml` to use it.
- Moved command validation, coercion, and dispatch out of QML.
- Kept unsupported commands visible but explicitly unavailable instead of silent no-ops.
- Fixed the Demo parameter mismatch by making Python consume the existing QML gimbal parameter names.

## Active Risks

- Stage 0 still lacks a durable merged authority-map artifact even though the initial discovery pass was completed.
- The broad QML context-property contract remains intentionally additive; Stage 1A reduced risk without yet reducing exposure count materially.

## Next Session Checklist

1. Decide whether the Stage 0 authority map should be merged as its own durable artifact before more implementation slices land.
2. Prepare `PLANNING.md` for Stage 1B settings outliers in `SettingsTab.qml`.
3. Keep `docs/tech-debt.md` and this tracker in sync when a slice moves from planned to implemented.