# Paint Controller — Repo Index

ROS2 node with PySide6/QML UI for robotic paint control on a Steam Deck. The live runtime is Python-first; the historical C++ UI path has been removed from the tree. Targets ROS2 Humble/Jazzy, Python 3.10+, and PySide6/Qt6.

## Current Strategy

- This branch is **refactor-first**. Runtime/workflow/service hardening, the QML flattening pass, the feature-root pass, and the completed ownership work through Workstream D are historical record now.
- The current architecture control plane is intentionally split in two: **`docs/plan/00_ARCHITECTURE_PROGRESS.md`** is the only live execution board, and **`docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`** is the durable architecture guide.
- The unfinished tail is no longer a generic structural cleanup. It is a family-by-family boundary retirement program focused on shrinking the permanent QML runtime surface.
- The current live next direction is settings cleanup, followed by bounded `app_runtime.py` and handler decomposition only where they preserve the current contracts and materially reduce ambient reads.
- Shell and launcher boundary work is treated as frozen unless a future slice proves a real retirement win that cannot be achieved inside the current contract.
- The former `PageHome.qml` preview remainder is retired behind explicit `videoRuntime` ownership, while `PageWheel.qml` base preview remains explicit quarantine.
- **Net-new feature work is intentionally deferred** until medium/high-priority debt is closed and the validation gates stay green (pytest, pyright for covered scope, ROS build, and offscreen startup/shutdown smoke).
- Low-priority design-system backlog may remain backlog. By default it is **not** the feature-blocking path unless the user explicitly reprioritizes.
- Latest verified local full-suite validation is `260 passed` on 2026-04-28 for `python/paint_controller/venv/bin/python -m pytest tests -q`. Most recent focused validation is green at `10 passed` for `tests/test_startup_smoke_home.py`, `tests/test_startup_smoke_shell.py`, and `tests/test_qml_imports.py`, with the follow-on workflow-editor import band green at `2 passed`.

---

## Session-Start Checklist

Read in this order at the start of any session:

1. **`INDEX.md`** (this file) — repo map and orientation
2. **`AGENTS.md`** — workflow rules, planning process, stop-and-ask triggers, and the Kimi CLI tool mapping (when to use plan mode, `TodoList`, subagents, etc.)
3. **`KNOWLEDGE.md`** — gotchas, patterns, anti-patterns. Check before debugging.
4. **`DEVNOTES.md`** — last 90 days of session notes and validation results
5. **`docs/plan/00_ARCHITECTURE_PROGRESS.md`** — current roadmap status, completed slices, next recommended slice
6. **`docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`** — durable architecture rationale, invariants, anti-goals, and historical completion context
7. **`docs/tech-debt.md`** — known debt items with priority and effort (check before starting new work)

---

## Authority Hierarchy

When two files disagree, prefer the file higher in this list:

| Priority | File | What it governs |
|---|---|---|
| 1 | `DEVNOTES.md` | Most recent verified runtime state |
| 2 | `docs/plan/00_ARCHITECTURE_PROGRESS.md` | Current live architecture board and execution order |
| 3 | `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` | Durable architecture rationale and historical context |
| 4 | `docs/tech-debt.md` | Known debt items, priorities, effort |
| 5 | `KNOWLEDGE.md` | Reusable patterns and gotchas |
| 6 | `README.md` | Operator/developer entry point |

---

## Code Structure Map

```
paint_controller_ros2/
│
├── python/paint_controller/       # Main Python application
│   ├── core/                      # Application bootstrap, ROS node, Qt bridge, state, settings
│   ├── controllers/               # Hardware controllers (ESP32, Teensy, winch, wheel, etc.)
│   ├── handlers/                  # Input processing, emergency, heartbeat, warnings
│   ├── services/                  # Video streaming, workflow execution, screen mgr
│   ├── models/                    # Lightweight state models, including joystick-selection ownership
│   ├── ui/                        # Overlay controller (non-QML)
│   ├── utils/                     # Pure utilities: CRC, input math, constants
│   ├── qml/                       # All QML UI components
│   │   ├── core/                  # MainWindow shell and compatibility QML shims
│   │   ├── theme/                 # Canonical design tokens (`CommonStyle`)
│   │   ├── features/              # Shared feature-root entry surfaces
│   │   │   ├── systemcontrol/     # Shared system-control workspace
│   │   │   └── video/             # Shared fullscreen-video workspace
│   │   ├── navigation/            # TopBar, SelectBar
│   │   ├── pages/                 # Full-page views (home, wheel, winch, settings, status, tuning)
│   │   ├── overlays/              # Overlay layers and compatibility wrappers
│   │   ├── components/            # Reusable UI components (buttons, displays, popups)
│   ├── config/                    # SSH/bash config JSON
│   └── resource/                  # Workflow JSON definitions
│
├── python/config/                 # Hardware config JSON (ESP32, settings defaults)
│
├── launch/                        # ROS2 launch files
├── tests/                         # pytest test suite
│   ├── conftest.py                # Fixtures, namespace stubs, Qt/ROS fakes setup
│   └── fakes.py                   # Shared fake ROS primitives (publisher, node, bus)
│
├── docs/
│   ├── plan/                      # Modernization plan tracker docs
│   │   ├── 00_ARCHITECTURE_PROGRESS.md          # Current roadmap status and next-slice tracker
│   │   └── 01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md  # Durable architecture rationale and historical context
│   ├── tech-debt.md               # Active tech debt tracker (living document)
│   └── devnotes/                  # Quarterly DEVNOTES cold-storage archives
│       └── 2026-Q1.md             # Jan–Mar 2026 session notes (archived)
│
├── AGENTS.md                      # Workflow rules for all LLM agents (canonical)
├── INDEX.md                       # This file — repo map and session-start guide
├── KNOWLEDGE.md                   # Extracted reusable patterns and gotchas
├── DEVNOTES.md                    # Rolling 90-day session notes
├── PLANNING.md                    # Active task scratch (temporary, delete before merge)
├── README.md                      # Operator/developer setup and run guide
```

---

## Key Commands

```bash
# Build ROS2 packages
cd ~/ros2_ws && colcon build --packages-select paint_interfaces paint_controller_ros2

# Run application
paint_controller

# Run tests (from repo root)
python/paint_controller/venv/bin/python -m pytest tests -q

# Run targeted tests
python/paint_controller/venv/bin/python -m pytest tests/test_control_processor.py -q
```

---

## Stale / Deprecated Files — Skip These

| File | Why stale |
|---|---|
| `PLANNING.md` | Temporary active-task scratch; if it exists, verify that it matches the currently approved task before trusting it |

Older notes may still mention `REFACTOR_TRACKER.md`; that historical tracker is no longer present in this repo and should be ignored.

---

## Environment Notes

- **VS Code interpreter**: use `python/paint_controller/venv/bin/python` for editor tooling and tests
- **`QT_QPA_PLATFORM`**: force-assigned `"offscreen"` in `tests/conftest.py` — overrides any shell-level `xcb`
- **Test suite**: full-suite baseline is `260 passed` on 2026-04-28 for `python/paint_controller/venv/bin/python -m pytest tests -q`; most recent focused result is also green for the fullscreen overlay startup-smoke + import band
- If PySide6 or pytest appear missing in-editor, check the selected interpreter first
