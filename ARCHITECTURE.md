# Architecture Guide

Human-oriented map of **how this program is structured**.

This document answers: *where does code live, who owns what, and how do pieces talk?*  
It does **not** cover operator UX, visual design, or industrial HMI certification.

| Need | Document |
|---|---|
| Session orientation & authority hierarchy | [`INDEX.md`](INDEX.md) |
| How to work in this repo (agents / gates) | [`AGENTS.md`](AGENTS.md) |
| Live unfinished architecture work | [`docs/plan/00_ARCHITECTURE_PROGRESS.md`](docs/plan/00_ARCHITECTURE_PROGRESS.md) |
| Durable rationale & invariants | [`docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`](docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md) |
| Known debt items | [`docs/tech-debt.md`](docs/tech-debt.md) |
| Run / install | [`README.md`](README.md) |

---

## 1. What This Application Is

A **ROS 2 + PySide6/QML** control application for a paint robot, typically run on a Steam Deck.

| Layer | Technology | Role |
|---|---|---|
| Frontend | QML (Qt 6) | Declarative views; binds to Python objects; calls slots |
| Backend | Python 3.10+ | Policy, hardware, ROS, safety, workflow, settings |
| Middleware | ROS 2 (Humble/Jazzy) | Device pub/sub and node lifecycle |
| Entry | `paint_controller` / `python -m paint_controller` | Thin main → `AppRuntime` |

The live tree is **Python-first**. There is no second UI stack in this repository.

---

## 2. Big Picture

```
┌──────────────────────────────────────────────────────────────────┐
│  QML  (python/paint_controller/qml/)                             │
│  pages · overlays · features · navigation · components           │
│  reads status / shell / settings · calls *Actions slots          │
└───────────────────────────────┬──────────────────────────────────┘
                                │  setContextProperty (~28 names)
                                │  assembled by QmlContextComposer
┌───────────────────────────────▼──────────────────────────────────┐
│  CORE  (python/paint_controller/core/)                           │
│  AppRuntime · ControllerFactory · SignalWiring                   │
│  QmlContextComposer · Settings · StateStore · QtBridge · ROS     │
└───────┬──────────────┬──────────────┬──────────────┬─────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
   models/        handlers/      services/     controllers/
   *Actions       teleop         video         device / ROS I/O
   gates          emergency      workflow
   shell          input          recording
   legality       safety         screen / SSH
        └──────────────┴──────────────┴──────────────┘
                                │
                                ▼
                         ROS 2 / hardware
```

**Rule of thumb**

- **QML** presents state and invokes commands.
- **Python** owns policy, persistence, machine-affecting behavior, and cross-surface decisions.
- **Controllers** talk to ROS/hardware; they are not raw QML globals.
- **Discrete operator commands** go through `*Actions` (+ gate). **Continuous teleop** goes through `ControlProcessor`.

---

## 3. Startup and Shutdown

Composition root: `python/paint_controller/core/app_runtime.py`  
Thin entry: `python/paint_controller/core/application.py`

### Startup (order of ideas)

1. Init ROS (`rclpy`), create the ROS node.
2. Create `QApplication` and core objects (`StateStore`, `SettingsManager`, …).
3. Start video / base-top services as needed.
4. Load the QML engine and main shell.
5. `create_controllers()` → `ControllerBundle` (dependency-injected graph).
6. `SignalWiring` — timers and cross-object signal connections.
7. `QmlContextComposer.compose()` — build the root context property map and `setContextProperty` each name.
8. Start status / control timers; enter the Qt event loop.

### Shutdown (order of ideas)

1. Stop status timers.
2. Tear down QML roots (`teardown_qml_runtime`) before backend `QObject` cleanup.
3. Stop ROS spin thread.
4. `ControllerBundle.cleanup()` in reverse creation order.
5. Clean video / base-top / HID / node.

If you change lifetime, timers, `QThread`s, or cleanup, prefer a teardown-focused test (see `tests/test_ssh.py` as a model).

---

## 4. Backend Package Map

Root package: `python/paint_controller/`

### `core/` — composition and shared runtime

| Module | Responsibility |
|---|---|
| `application.py` | Process entry; signal handlers; create `AppRuntime` |
| `app_runtime.py` | **Composition root**: startup, exec, shutdown |
| `controller_factory.py` | Build `ControllerBundle`; reverse-order `cleanup()` |
| `qml_context_composer.py` | Assemble QML root context + status wrapper QObjects |
| `signal_wiring.py` | Timers and production signal graph (e.g. status tick → teleop) |
| `settings.py` | Settings schema, persistence, QML-facing settings API |
| `state_store.py` | Shared runtime state (heartbeat class, messages, …) |
| `qt_bridge.py` | Small UI bridge signals (popups, sidebar, video requests) |
| `ros_node.py` | ROS node helpers + `RosThread` (spin off the GUI thread) |
| `config.py` | Runtime defaults (e.g. control update rate) |

### `controllers/` — device / ROS adapters

Hardware- and ROS-facing `QObject`s. They publish/subscribe and expose status.

Examples: `teensy`, `winch`, `wheel`, `esp32_valve`, `lidar`, `ssh`, `system_monitor`, `wind_monitor`.

- Base helpers: `controllers/_base.py`
- **Do not import handlers/models/QML from controllers** — keep this layer leaf-like for testing.

### `handlers/` — cross-cutting runtime behavior

| Area | Examples |
|---|---|
| Continuous control | `control_processor.py` — joystick axes → hardware at rate limits |
| Input / HID | `steam_deck.py`, `input.py` |
| Safety | `emergency.py`, `safety_coordinator.py`, `heartbeat.py` |
| Residual command surface | `device_actions.py` (legacy-ish; prefer feature `*Actions` for new work) |
| Other | `manual_commands.py`, `warnings.py` |

### `models/` — QML-facing application models (not pure domain DTOs)

Despite the name, these are mostly **QObjects** that form the stable API toward QML:

| Kind | Examples | Role |
|---|---|---|
| Command models | `winch_actions`, `wheel_actions`, `teensy_actions`, `tuning_actions`, `recording_actions`, `system_actions`, `base_top_view_actions` | `@Slot` methods; call `AdminActionGate` then controllers |
| Policy | `admin_action_gate`, `action_legality_model`, `capability_catalog` | Legality metadata + enforcement seam |
| Shell | `shell_state`, `shell_router`, `overlay_host_policy` | Routes, dual-surface policy, overlay placement |
| Selection | `joystick_selection` | Control-mode / selection ownership |

**Preferred write path from QML:** `someActions.doThing(...)` → gate → controller.

### `services/` — longer-running app services

| Area | Examples |
|---|---|
| Video | `video_stream.py`, `base_top_view_service.py` |
| Workflow | `services/workflow/*` (catalog, editor, runner, executor, scheduler) |
| Capture / screens | `screen_manager`, `screen_recorder`, `ros_bag_recorder` |

### `ui/` · `widgets/` · `utils/`

| Package | Role |
|---|---|
| `ui/` | Non-QML UI helpers (e.g. `overlay.py` controller) |
| `widgets/` | Native widgets (e.g. VTK point cloud) when needed outside pure QML |
| `utils/` | Pure helpers: CRC, input math, constants, Qt env, HID |

---

## 5. Frontend Package Map (QML as code)

Root: `python/paint_controller/qml/`

```
qml/
├── core/           MainWindow, MultiScreenHost — shell hosts
├── theme/          CommonStyle (design tokens; optional for structure)
├── features/       Shared feature-root workspaces
│   ├── systemcontrol/
│   └── video/
├── navigation/     TopBar, SelectBar, connection chrome
├── pages/          Full routes (home, wheel, winch, settings, status, tuning, …)
├── overlays/       Overlay layers (system control tabs, video, emergency, lidar, …)
└── components/     Reusable buttons, displays, popups
```

Each folder typically has a `qmldir`. Imports are mostly **relative** (`import "../theme"`).

### How QML is supposed to use Python

1. **Read** operator-facing status from named context objects (`winchStatus`, `teensyStatus`, `videoRuntime`, …).
2. **Write / command** through `*Actions` slots (`winchActions`, `wheelActions`, …), not by grabbing controllers.
3. **Shell / navigation** through `shellRouter`, `shellState`, `overlayHost`.
4. **Feature roots** (`features/…`) receive dependencies via `required property` injection from the shell when possible, instead of reaching for every global.

Large leaves (e.g. `pages/winch/PageWinch.qml`, workflow editor tabs) still concentrate a lot of logic; prefer extracting components and moving document/policy logic into Python when you touch them.

---

## 6. The QML ↔ Python Contract

Context properties are registered with `engine.rootContext().setContextProperty(name, obj)`.

**Source of truth for the name list:**  
`python/paint_controller/core/qml_context_composer.py` → `_EXPECTED_CONTEXT_PROPERTY_NAMES`

Rough groups (names as exposed to QML):

| Group | Examples | Purpose |
|---|---|---|
| Shell / host | `shellState`, `shellRouter`, `overlayHost` | Route identity, dual-monitor policy, overlay layers |
| Feature bundles | `systemControlServices`, `videoRuntime` | Workflow/editor/commands; fullscreen video family |
| Status (read) | `wheelStatus`, `winchStatus`, `teensyStatus`, `valveStatus`, `lidarStatus`, `recordingStatus`, `shellConnectivityStatus`, `baseTopViewStatus` | Telemetry façades for QML bindings |
| Commands (write) | `wheelActions`, `winchActions`, `teensyActions`, `tuningActions`, `recordingActions`, `systemActions`, `baseTopViewActions` | Gated machine-affecting slots |
| Legality | `actionLegality` | UI can query whether an action is allowed |
| Admin / launcher | `launcherAdmin` | Launcher-side admin actions |
| Settings | `settingsManager` | Schema-backed settings (also used for writes today) |
| Misc / residual | `stateStore`, `backend`, `deviceActionHandler`, `overlayController`, `warningHandler` | Shared state, thin UI bridge, older device-action surface |

### Rules that keep the contract honest

- Prefer **new work** on status + `*Actions` owners, not new raw controller globals.
- If you **add or remove** a root context property, update:
  1. `QmlContextComposer` / `_EXPECTED_CONTEXT_PROPERTY_NAMES`
  2. Startup-smoke fixtures (`tests/startup_smoke_support.py` and related)
  3. Any tests that assert the public name set
- Do **not** use `qmlRegisterSingletonInstance()` in this repo (use context properties).

---

## 7. Two Runtime Paths for Machine Behavior

Understanding these two paths avoids putting code in the wrong place.

### A. Discrete commands (buttons, admin actions)

```
QML slot call
  → models/*Actions  (or residual deviceActionHandler)
  → AdminActionGate.check_action(...)
  → controller / service method
  → ROS / hardware
```

- Legality metadata lives in `capability_catalog` / gate.
- QML may also consult `actionLegality` to disable controls; **Python still enforces**.

### B. Continuous teleop (sticks / axes)

```
Steam Deck HID thread
  → SteamDeckHandler (main thread edges / state)
SignalWiring status timer (~60 Hz default)
  → ControlProcessor.process_input(...)
  → rate-limited publishes on controllers
```

- This path is **not** the same as per-button `AdminActionGate` slots.
- Effector-specific locks and rate limits live in `ControlProcessor`.
- Shared hard stop sequence lives in `SafetyCoordinator.halt_all_effectors()` (used by emergency, heartbeat, motor fault paths).

When adding a new “hold button to move” vs “tap to home” behavior, pick the path deliberately.

---

## 8. Threading (program view)

| Thread / affinity | Typical residents |
|---|---|
| **Qt GUI / main** | `AppRuntime`, QML engine, most `QObject` controllers as API surface, `ControlProcessor`, status timer |
| **ROS spin** | `RosThread` — `rclpy.spin_once` isolated from the GUI |
| **HID** | Steam Deck reader thread → signals to main |
| **Video / vision workers** | GStreamer sample callbacks; base-top OpenCV worker; image providers under mutex |
| **Other workers** | e.g. system monitor `moveToThread`, ESP32 UDP receive, workflow executor |

House rules (see also `KNOWLEDGE.md`):

- Prefer **emit outside locks**.
- Cross-thread edges: prefer explicit `Qt.QueuedConnection` when affinity is known.
- Video: copy under lock; drop frames under load rather than unbounded queues.
- Shutdown: stop UI/timers → tear down QML → join workers → ROS → destroy node.

---

## 9. Configuration and Resources

| Location | Contents |
|---|---|
| `python/config/` | Hardware / defaults JSON (e.g. `settings.json`, device configs) |
| `python/paint_controller/config/` | SSH / bash helper config |
| `python/paint_controller/resource/` | Images, workflow YAML samples |
| Settings runtime | `SettingsManager` loads/persists schema-driven values (path details evolve; see tech debt if deploying read-only) |

---

## 10. Tests and How They Mirror Architecture

| Concern | Where |
|---|---|
| Fixtures, offscreen Qt, package stubs | `tests/conftest.py` |
| Shared ROS fakes | `tests/fakes.py` |
| QML startup smoke + contract fakes | `tests/startup_smoke_support.py`, `test_startup_smoke*.py` |
| Factory / runtime / composer | `test_controller_factory_runtime.py`, `test_app_runtime_runtime.py`, `test_qml_context_composer.py` |
| Action gates / models | `test_*_actions.py`, `test_admin_action_gate.py`, … |
| Wiring | `test_signal_wiring.py`, `test_notify_contracts.py` |

**Important harness facts**

- `QT_QPA_PLATFORM` is force-set to `offscreen` in tests (must not be only `setdefault`).
- Top-level packages may be stubbed as empty modules so pure-Python tests avoid heavy imports.
- `qt_core_app` is an alias of `qt_app` — do not create a second `QCoreApplication`.

Run:

```bash
python/paint_controller/venv/bin/python -m pytest tests -q
```

---

## 11. How to Extend the Program

### Add a **gated operator action** (preferred)

1. Implement or extend the device method on the **controller** (or service).
2. Add a `@Slot` on the relevant `models/*_actions.py` (or a new `*Actions` if it is a new family).
3. Register the action in **capability / gate** metadata if legality applies.
4. Ensure the actions object is already on the context map (or add it carefully — see contract rules).
5. Call the slot from QML; bind enablement via `actionLegality` if useful.
6. Unit-test the action + gate denial path; update smoke if the root contract changed.

### Add a **new device / telemetry family**

1. `controllers/<device>.py` (+ `_base` if it fits).
2. Wire construction + cleanup in `controller_factory.py` / `ControllerBundle`.
3. Expose **status** for QML (prefer a dedicated status QObject owned near the producer; today many live as wrappers in `qml_context_composer.py`).
4. Expose **commands** via `*Actions`, not raw controller on the root context.
5. Update `_EXPECTED_CONTEXT_PROPERTY_NAMES` + startup-smoke fakes + tests.
6. Add QML page/overlay only after the Python contract exists.

### Add **continuous teleop** for an axis

1. Extend input sampling / mapping as needed (`steam_deck` / input utils).
2. Teach `ControlProcessor` rate limits and publish path.
3. Do not only add a QML button slot if the behavior is continuous stick control.

### Things to avoid

- Putting safety, actuator math, or emergency policy in QML.
- Re-introducing raw `*Controller` objects as new root context properties.
- A mega-`Backend` façade that only renames ambient access.
- New equal-owner paths for the same operator-visible behavior (two modules that both “own” the same command).

---

## 12. Ownership Cheat Sheet

| Concern | Canonical owner (Python) |
|---|---|
| Process lifetime / composition | `AppRuntime` |
| Object graph construction | `controller_factory` / `ControllerBundle` |
| QML root property map | `QmlContextComposer` |
| Timer + production signal graph | `SignalWiring` |
| Route identity / navigation API | `ShellRouter` (+ shell QML map) |
| Dual-surface / shell policy flags | `ShellState` |
| Overlay host & z-layer policy | `OverlayHostPolicy` (`overlayHost` in QML) |
| Discrete admin / device commands | Feature `*Actions` + `AdminActionGate` |
| Continuous motion from sticks | `ControlProcessor` |
| Halt-all effectors | `SafetyCoordinator` |
| Settings schema & persistence | `SettingsManager` |
| Workflow run / edit | `services/workflow/*` via `systemControlServices` (and related) |
| Fullscreen video family (touched surface) | `videoRuntime` |

Frozen contracts and quarantine exceptions are listed on the live board:  
[`docs/plan/00_ARCHITECTURE_PROGRESS.md`](docs/plan/00_ARCHITECTURE_PROGRESS.md).

---

## 13. Mental Model for Reading Code

When you open a PR or debug a bug, ask:

1. **Is this presentation or policy?** → QML vs Python.
2. **Is this a tap command or a continuous axis?** → `*Actions` vs `ControlProcessor`.
3. **Who is the single owner of this behavior?** → use the cheat sheet; avoid a second path.
4. **Is this on the QML root contract?** → if yes, composer + smoke must stay in sync.
5. **Does this touch threads or cleanup?** → follow shutdown order; add teardown coverage.

That is enough to navigate most of the tree without reading every file.

---

## 14. Related Paths (quick)

```
paint_controller_ros2/
├── ARCHITECTURE.md          ← this file
├── INDEX.md                 ← session map & authority
├── AGENTS.md                ← contributor/agent workflow
├── README.md                ← install & run
├── docs/plan/               ← live board + durable plan
├── docs/tech-debt.md
├── tests/
└── python/paint_controller/
    ├── core/
    ├── controllers/
    ├── handlers/
    ├── models/
    ├── services/
    ├── qml/
    ├── ui/
    ├── widgets/
    └── utils/
```
