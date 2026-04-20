# Paint Controller — Repo Index

ROS2 node with PySide6/QML UI for robotic paint control on a Steam Deck. Hybrid Python + C++ codebase targeting ROS2 Humble/Jazzy, Python 3.10+, and PySide6/Qt6.

---

## Session-Start Checklist

Read in this order at the start of any session:

1. **`INDEX.md`** (this file) — repo map and orientation
2. **`AGENTS.md`** — workflow rules, planning process, stop-and-ask triggers
3. **`KNOWLEDGE.md`** — gotchas, patterns, anti-patterns. Check before debugging.
4. **`DEVNOTES.md`** — last 90 days of session notes and validation results
5. **`docs/plan/01_MASTER_PLAN.md`** — authoritative task tracker and next-task gate
6. **`docs/tech-debt.md`** — known debt items with priority and effort (check before starting new work)
7. **`docs/plan/02_ARCHITECTURE.md`** — current runtime architecture (read if touching core)
8. **`docs/plan/03_QML_BINDINGS.md`** — QML↔Python registration state (read if touching QML)

---

## Authority Hierarchy

When two files disagree, prefer the file higher in this list:

| Priority | File | What it governs |
|---|---|---|
| 1 | `DEVNOTES.md` | Most recent verified runtime state |
| 2 | `docs/plan/01_MASTER_PLAN.md` | Task progress and completion status |
| 3 | `docs/tech-debt.md` | Known debt items, priorities, effort |
| 4 | `KNOWLEDGE.md` | Reusable patterns and gotchas |
| 4 | `docs/plan/02_ARCHITECTURE.md` | Runtime architecture |
| 5 | `README.md` | Operator/developer entry point |
| 6 | `docs/plan/03_QML_BINDINGS.md` | QML binding state |

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
│   ├── models/                    # Action/workflow config data models
│   ├── ui/                        # Overlay controller (non-QML)
│   ├── utils/                     # Pure utilities: CRC, input math, constants
│   ├── qml/                       # All QML UI components
│   │   ├── core/                  # MainWindow, CommonStyle theme tokens
│   │   ├── navigation/            # TopBar, SelectBar
│   │   ├── pages/                 # Full-page views (home, spray, wheel, winch, settings, status, etc.)
│   │   ├── overlays/              # Overlay layers (video, emergency, system control)
│   │   ├── components/            # Reusable UI components (buttons, inputs, displays, popups)
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
│   │   ├── 00_README.md           # Plan-docs navigation (narrower scope than INDEX.md)
│   │   ├── 01_MASTER_PLAN.md      # Active task tracker
│   │   ├── 02_ARCHITECTURE.md     # Runtime architecture reference
│   │   ├── 03_QML_BINDINGS.md     # QML registration state
│   │   └── 04_AUDIT_REPORT.md     # Historical pre-mortem (read-only reference)
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
└── REFACTOR_TRACKER.md            # Historical context only — do not use as active tracker
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
| `REFACTOR_TRACKER.md` | Historical context only; `01_MASTER_PLAN.md` + `docs/tech-debt.md` are the active trackers |
| `docs/plan/04_AUDIT_REPORT.md` | Pre-mortem rationale; some recommendations were superseded |
| `PLANNING.md` | Temporary active-task scratch; should not exist between sessions |

---

## Environment Notes

- **VS Code interpreter**: pinned to `python/paint_controller/venv/bin/python` in `.vscode/settings.json`
- **`QT_QPA_PLATFORM`**: force-assigned `"offscreen"` in `tests/conftest.py` — overrides any shell-level `xcb`
- **Test suite**: use the venv python and revalidate the current full-suite status before commit; historical fixed test-count snapshots in older docs can drift
- If PySide6 or pytest appear missing in-editor, check the selected interpreter first
