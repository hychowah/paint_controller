# Tech Debt Tracker

Living document. Update when debt is discovered, addressed, or re-prioritised.

**Priority**: `high` = blocking quality or correctness | `medium` = degrades maintainability | `low` = cosmetic / nice-to-have

---

## Active Debt

### TD-001 — QML `required` properties not enforced
**Area**: QML UI  
**Priority**: medium  
**Effort**: medium (5 sub-tasks across component categories)  
**Why it matters**: Without `required`, QML silently ignores missing bindings. Components accept `undefined` values with no runtime error, making integration bugs invisible until runtime visual failures occur.  
**What to do**: Add `required` keyword to all bindable properties across buttons, inputs, displays, panels/popups, and widgets.  
**Related tasks**: `1.11a–e` in `docs/plan/01_MASTER_PLAN.md`  
**Files**: `qml/components/buttons/`, `qml/components/inputs/`, `qml/components/displays/`, `qml/components/panels/`, `qml/widgets/`

---

### TD-002 — Design system incomplete (video overlays, settings/status pages)
**Area**: QML UI  
**Priority**: medium  
**Effort**: medium  
**Why it matters**: Hardcoded colours, spacing, and font sizes in un-migrated files will diverge from the rest of the UI and make theme-wide changes expensive later.  
**What to do**: Migrate remaining QML to `CommonStyle` tokens: video overlays (`2.5c`), settings pages (`2.6b`), status/workflow pages (`2.6c`), systemcontrol tabs remainder (`2.5b`), `OverlayLayer` dedup (`2.7`), page renaming (`2.8`).  
**Related tasks**: `2.5b`, `2.5c`, `2.6b`, `2.6c`, `2.7`, `2.8` in `docs/plan/01_MASTER_PLAN.md`  
**Files**: `qml/overlays/video/`, `qml/pages/settings/`, `qml/pages/status/`, `qml/overlays/systemcontrol/`, `qml/overlays/OverlayLayer.qml`

---

### TD-003 — `__init__.py` re-exports pollute import graph
**Area**: Python packaging  
**Priority**: medium  
**Effort**: low  
**Why it matters**: Package `__init__.py` files re-export heavy dependencies (PySide6, rclpy) causing the full import chain to load in tests and any partial-import scenario. Test isolation currently relies on conftest namespace stubs as a workaround.  
**What to do**: Empty or remove cross-package re-exports from `__init__.py` files. Move shared symbols to lightweight `utils/` modules.  
**Related tasks**: `3.0` in `docs/plan/01_MASTER_PLAN.md`  
**Files**: `python/paint_controller/core/__init__.py`, `python/paint_controller/handlers/__init__.py`, `python/paint_controller/controllers/__init__.py`

---

### TD-004 — `workflow_legacy.py` not removed
**Area**: Services  
**Priority**: low  
**Effort**: low  
**Why it matters**: Dead code adds cognitive overhead, inflates search results, and may confuse agents about which workflow implementation is active.  
**What to do**: Confirm `workflow_legacy.py` has no live callers; delete it.  
**Files**: `python/paint_controller/services/workflow_legacy.py`

---

### TD-005 — WheelController has no unit tests
**Area**: Testing  
**Priority**: medium  
**Effort**: low  
**Why it matters**: WheelController handles safety-critical commands (wheel speed, emergency stop). The absence of tests leaves command-rejection guards and clamping unverified.  
**What to do**: Add unit tests following the `test_winch.py` pattern — fake bus transport, availability guards, clamp behaviour.  
**Related tasks**: `3.6` in `docs/plan/01_MASTER_PLAN.md`  
**Files**: `tests/test_wheel.py` (to create), `python/paint_controller/controllers/wheel.py`

---

### TD-006 — ESP32ValveController and TeensyController have no unit tests
**Area**: Testing  
**Priority**: medium  
**Effort**: medium  
**Why it matters**: Hardware controllers are safety-adjacent (valve position commands, relay/enable state). No tests means regression risk on socket, keepalive, or range-conversion bugs.  
**What to do**: Add unit tests for UDP keepalive, range conversion (×10/÷100), socket lock behaviour (ESP32), and user-field preservation (Teensy).  
**Related tasks**: `3.7` in `docs/plan/01_MASTER_PLAN.md`  
**Files**: `tests/test_esp32_valve.py` (to create), `tests/test_teensy.py` (to create), `python/paint_controller/controllers/esp32_valve.py`, `python/paint_controller/controllers/teensy.py`

---

### TD-007 — SteamDeck HID input parsing untested
**Area**: Testing  
**Priority**: low  
**Effort**: low  
**Why it matters**: Raw HID byte parsing is error-prone. Silent mis-mapping of buttons would cause incorrect commands without any visible failure.  
**What to do**: Add unit tests for `steam_deck.py` HID parsing: button bitmask extraction, axis normalisation, edge cases (all-zero, all-max, disconnected).  
**Related tasks**: `3.5` in `docs/plan/01_MASTER_PLAN.md`  
**Files**: `tests/test_steam_deck.py` (to create), `python/paint_controller/handlers/steam_deck.py`

---

### TD-008 — `toggle_multiscreen_window()` still uses `engine.rootObjects()[0]`
**Area**: Python / QML boundary  
**Priority**: low  
**Effort**: low  
**Why it matters**: Direct `rootObjects()` access is fragile — it couples Python to the QML object tree position and bypasses the signal/context-property pattern used everywhere else.  
**What to do**: Replace with a signal or context-property callable, matching the pattern established in task 1.2.  
**Files**: `python/paint_controller/core/application.py` (`toggle_multiscreen_window`)

---

## Resolved Debt

| ID | Title | Resolved | Notes |
|---|---|---|---|
| — | `qmlRegisterSingletonInstance` crashes | 2026-04-17 | Replaced with `setContextProperty` — see KNOWLEDGE.md |
| — | `findChild()` Python-side QML lookup | 2026-04-20 | Replaced with injected `close_popup_fn` callable |
| — | 4 winch move-command guards disabled | 2026-04-20 | Re-enabled with `get_logger().warning()` + early return |
| — | Dual-inheritance `RobotController` god class | pre-2026-04-17 | Split into `PaintRosNode`, `StateStore`, `QtBridge`, `ControllerFactory` |
| — | Hardcoded ESP32 MAC/IP in source | pre-2026-04-17 | Externalised to `python/config/esp32_valve.json` |
