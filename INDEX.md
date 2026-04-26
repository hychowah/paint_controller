# Paint Controller — Repo Index

ROS2 node with PySide6/QML UI for robotic paint control on a Steam Deck. The live runtime is Python-first; the historical C++ UI path has been removed from the tree. Targets ROS2 Humble/Jazzy, Python 3.10+, and PySide6/Qt6.

## Current Strategy

- This branch is **refactor-first**. Runtime/workflow/service validation hardening is complete, and **`TD-001` Stage 1 is complete**: verified-dead QML was removed, false shared-component folders were flattened, constructor-driven QML surfaces were hardened with `required` / `readonly`, startup/import smoke coverage was expanded, and warn-only `qmllint` CI is now in place.
- **`TD-031` is complete**: the page registry is explicit, `systemcontrol` and fullscreen video now have dedicated feature roots, and canonical theme ownership lives under `qml/theme/CommonStyle.qml`. Focused smoke coverage was expanded to the new feature roots; compatibility wrappers remain intentionally to keep import churn out of the blocking stage.
- The QML cleanup is intentionally split into **two stages**. Stage 1 was the safe flatten + hardening batch; Stage 2 is the narrowed `TD-031` structural pass. URI-module migration, broad lidar/pointcloud restructuring, and any optional root-file rename are explicitly out of scope for this stage.
- The current architecture direction is tracked in **`docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`** and the current slice status is tracked in **`docs/plan/00_ARCHITECTURE_PROGRESS.md`**. **Stage 1A through Stage 1E, Stage 2, Stage 3A, and Stage 4 are complete**: the live `OverlayController` / `ControlProcessor` cycle is gone, joystick selection ownership lives in `JoystickSelectionModel`, shell policy now lives in a narrow `ShellState`, the Settings route is now truthful where schema-backed settings exist, and the next recommended implementation path is **Stage 3B1 route normalization**.
- **Net-new feature work is intentionally deferred** until medium/high-priority debt is closed and the validation gates stay green (pytest, pyright for covered scope, ROS build, and offscreen startup/shutdown smoke).
- Low-priority design-system backlog may remain backlog. By default it is **not** the feature-blocking path unless the user explicitly reprioritizes.
- Latest verified local validation on 2026-04-26 is green at `210 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. Focused Stage 4 slices are green for `tests/test_capability_catalog.py`, `tests/test_controller_factory_runtime.py`, `tests/test_settings_runtime.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`.

---

## Session-Start Checklist

Read in this order at the start of any session:

1. **`INDEX.md`** (this file) — repo map and orientation
2. **`AGENTS.md`** — workflow rules, planning process, stop-and-ask triggers
3. **`KNOWLEDGE.md`** — gotchas, patterns, anti-patterns. Check before debugging.
4. **`DEVNOTES.md`** — last 90 days of session notes and validation results
5. **`docs/plan/00_ARCHITECTURE_PROGRESS.md`** — current roadmap status, completed slices, next recommended slice
6. **`docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`** — active architecture roadmap and stage order
7. **`docs/tech-debt.md`** — known debt items with priority and effort (check before starting new work)

---

## Authority Hierarchy

When two files disagree, prefer the file higher in this list:

| Priority | File | What it governs |
|---|---|---|
| 1 | `DEVNOTES.md` | Most recent verified runtime state |
| 2 | `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` | Active architecture roadmap and stage order |
| 3 | `docs/tech-debt.md` | Known debt items, priorities, effort |
| 4 | `KNOWLEDGE.md` | Reusable patterns and gotchas |
| 5 | `README.md` | Operator/developer entry point |

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
│   │   └── 01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md  # Active architecture roadmap
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
- **Test suite**: latest verified local full-suite status is `210 passed` on 2026-04-26; focused Stage 4 settings/capability slices are also green; revalidate with the venv python before commit if you need a fresher claim
- If PySide6 or pytest appear missing in-editor, check the selected interpreter first
