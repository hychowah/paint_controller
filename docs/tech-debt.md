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
**What to do**: Add `required` keyword to all bindable properties across buttons, inputs, displays, panels/popups, and the surviving specialized reusable QML components. Run this only after the controller/input safety-test queue is stronger.  
**Related tasks**: `1.11a–e` in `docs/plan/01_MASTER_PLAN.md`  
**Files**: `qml/components/buttons/`, `qml/components/inputs/`, `qml/components/displays/`, `qml/components/panels/`, `qml/components/popups/`, `qml/components/specialized/`

---

### TD-002 — Design system incomplete (video overlays, settings/status pages)
**Area**: QML UI  
**Priority**: low  
**Effort**: medium  
**Why it matters**: Hardcoded colours, spacing, and font sizes in un-migrated files will diverge from the rest of the UI and make theme-wide changes expensive later.  
**What to do**: Resume the remaining `CommonStyle` rollout only after the active bug-fix and controller/input test-hardening queue is complete. Remaining scope: video overlays (`2.5c`), settings pages (`2.6b`), status/workflow pages (`2.6c`), systemcontrol tabs remainder (`2.5b`), and `OverlayLayer` dedup (`2.7`).  
**Related tasks**: `2.5b`, `2.5c`, `2.6b`, `2.6c`, `2.7` in `docs/plan/01_MASTER_PLAN.md`  
**Files**: `qml/overlays/video/`, `qml/pages/settings/`, `qml/pages/status/`, `qml/overlays/systemcontrol/`, `qml/overlays/OverlayLayer.qml`

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

### TD-014 — `main()` god-function
**Area**: Python / Application  
**Priority**: medium  
**Effort**: medium  
**Why it matters**: `core/application.py` `main()` is ~265 lines with 10+ responsibilities. Untestable as a unit and hard to navigate.  
**What to do**: Extract into named functions: `_create_core_objects`, `_create_video_services`, `_setup_qml_engine`, `_register_context_properties`, `_wire_signals`, `_start_timers`, `_cleanup`. Move `RosThread` to `core/ros_node.py`.  
**Files**: `python/paint_controller/core/application.py`

---

### TD-016 — `VideoOverlayStyle.qml` parallel style system
**Area**: QML UI  
**Priority**: low  
**Effort**: low  
**Why it matters**: `VideoOverlayStyle.qml` is a ~30-token style system that duplicates tokens in `CommonStyle`. Two style sources make theme-wide changes require double edits.  
**What to do**: Merge into `CommonStyle` or make a domain-specific extension that derives from it (co-located tokens, shared base).  
**Files**: `python/paint_controller/qml/overlays/video/components/VideoOverlayStyle.qml`

---

## Resolved Debt

| ID | Title | Resolved | Notes |
|---|---|---|---|
| — | `qmlRegisterSingletonInstance` crashes | 2026-04-17 | Replaced with `setContextProperty` — see KNOWLEDGE.md |
| — | `findChild()` Python-side QML lookup | 2026-04-20 | Replaced with injected `close_popup_fn` callable |
| — | 4 winch move-command guards disabled | 2026-04-20 | Re-enabled with `get_logger().warning()` + early return |
| — | Dual-inheritance `RobotController` god class | pre-2026-04-17 | Split into `PaintRosNode`, `StateStore`, `QtBridge`, `ControllerFactory` |
| — | Hardcoded ESP32 MAC/IP in source | pre-2026-04-17 | Externalised to `python/config/esp32_valve.json` |
| TD-004 | `workflow_legacy.py` not removed | 2026-04-20 | Deleted in Phase 1B along with full legacy workflow system (11 files) |
| TD-003 | `__init__.py` re-exports pollute import graph | 2026-04-20 | Fixed in task `3.0` — subpackage `__init__.py` files are now lightweight and no longer re-export heavy Qt/ROS modules |
| TD-005 | WheelController has no unit tests | 2026-04-20 | Fixed in task `3.6` — `tests/test_wheel.py` now covers unified speed publishing, status updates, error transitions, and timeout availability |
| TD-006 | ESP32ValveController and TeensyController have no unit tests | 2026-04-20 | Fixed in task `3.7` — `tests/test_esp32_valve.py` and `tests/test_teensy.py` now cover protocol conversion, keepalive/status behavior, user-field preservation, and thrust/force publishing |
| TD-012 | Workflow executor thread safety | 2026-04-20 | Fixed in Phase 0A — `threading.Lock` + `threading.Event` property wrappers |
| TD-013 | Workflow DI bypass (hardware controllers silently `None`) | 2026-04-20 | Fixed in Phase 0B — `HardwareControllers.from_controllers()` explicit DI |
| TD-015 | `BirdViewService` dead code | 2026-04-20 | Deleted in Phase 1C — `bird_view_service.py` + `PointEditorOverlay.qml` removed |
| TD-008 | `toggle_multiscreen_window()` still uses `engine.rootObjects()[0]` | 2026-04-20 | Dropped from the active debt list after review — single stable call site, not worth replacing right now |
| TD-017 | `show_popup_fn` constructor coupling | 2026-04-20 | Dropped from the active debt list after review — callable injection is acceptable DI, not harmful debt |
