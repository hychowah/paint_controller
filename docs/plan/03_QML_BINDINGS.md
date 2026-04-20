# QML ↔ Python Bindings Inventory

> **Source**: Codebase review (2026-04). Updated 2026-04-17 with implementation progress.
> **Canonical location**: `docs/plan/03_QML_BINDINGS.md`
> **Related**: [01_MASTER_PLAN.md](01_MASTER_PLAN.md) | [02_ARCHITECTURE.md](02_ARCHITECTURE.md) | [04_AUDIT_REPORT.md](04_AUDIT_REPORT.md)

---

## QML Engine Setup

**Location**: `python/paint_controller/core/application.py`

### Engine Initialization
```python
engine = QQmlApplicationEngine()
engine.addImageProvider("ef_live", video_stream_handler.ef_image_provider)
engine.addImageProvider("base_front_live", video_stream_handler.front_image_provider)
engine.addImageProvider("base_rear_live", video_stream_handler.rear_image_provider)
engine.addImageProvider("base_top_view", base_top_view_service.image_provider)

# Add QML import path
qml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qml')
engine.addImportPath(qml_dir)

# Register context properties BEFORE engine.load()
ctx = engine.rootContext()
ctx.setContextProperty("stateStore", state_store)
# ... all other setContextProperty calls ...

qml_path = os.path.join(qml_dir, 'core', 'MainWindow.qml')
engine.load(QUrl.fromLocalFile(qml_path))
```

---

## Current Runtime Registration State

As of 2026-04-20, all 22 runtime objects are exposed via `setContextProperty()`. A validation loop in `application.py` verifies all 22 are non-`None` after `engine.load()`.

> **⚠️ DO NOT USE `qmlRegisterSingletonInstance()` in PySide6.**
> It corrupts the QML type system when combined with implicit directory imports (no `qmldir`).
> Symptoms: `Cannot assign object of type "QQuickRectangle" to list property "data"` — global breakage.
> See KNOWLEDGE.md entry "NEVER Use qmlRegisterSingletonInstance in PySide6" and PYSIDE-2173/2160/2310.

- All runtime objects use `engine.rootContext().setContextProperty()`
- QML accesses them via lowercase instance names (e.g., `stateStore.control_mode`)
- Removed aliases `baseStreamer` and `videoStreamer` are no longer part of the live Python/QML path

### Core Objects
| Property Name | Source | Type | Migration Task |
|---|---|---|---|
| `backend` | `qt_bridge` | `QtBridge` | Task 1.2 ✅ (signals implemented, findChild eliminated) |
| `overlayController` | `bundle.overlay_controller` | `OverlayController` | Context property retained; no singleton migration planned |
| `controlProcessor` | `bundle.control_processor` | `ControlProcessor` | Context property retained; no singleton migration planned |

### Hardware Controllers
| Property Name | Source | Type | Migration Task |
|---|---|---|---|
| `wheelController` | `bundle.wheel_controller` | `WheelController` | Context property retained; no singleton migration planned |
| `winchController` | `bundle.winch_controller` | `WinchController` | Context property retained; no singleton migration planned |
| `teensyController` | `bundle.teensy_controller` | `TeensyController` | Context property retained; no singleton migration planned |
| `esp32ValveController` | `bundle.esp32_valve_controller` | `ESP32ValveController` | Context property retained; no singleton migration planned |
| `lidarController` | `bundle.lidar_controller` | `LidarController` | Context property retained; no singleton migration planned |
| `windMonitor` | `bundle.wind_monitor` | `WindMonitor` | Context property retained; no singleton migration planned |

### Services
| Property Name | Source | Type | Migration Task |
|---|---|---|---|
| `workFlowRunner` | `bundle.workflow_runner` | `WorkFlowRunner` | Context property retained; active runtime path |
| `baseStreamHandler` | `video_stream_handler` | `VideoStreamHandler` | Context property retained; no singleton migration planned |
| `baseTopViewController` | `base_top_view_service` | `BaseTopViewService` | Context property retained; no singleton migration planned |

### System & UI
| Property Name | Source | Type | Migration Task |
|---|---|---|---|
| `warningHandler` | `bundle.warning_handler` | `WarningHandler` | Context property retained; no singleton migration planned |
| `heartbeatHandler` | `bundle.heartbeat_handler` | `UIHeartbeatHandler` | Context property retained; no singleton migration planned |
| `sshHandler` | `bundle.ssh_controller` | `UISSHController` | Context property retained; no singleton migration planned |
| `systemMonitor` | `bundle.system_monitor` | `SystemMonitor` | Context property retained; no singleton migration planned |
| `screenManager` | `bundle.screen_manager` | `ScreenManager` | Context property retained; no singleton migration planned |
| `screenRecorder` | `bundle.screen_recorder` | `ScreenRecorder` | Context property retained; no singleton migration planned |
| `rosBagRecorder` | `bundle.ros_bag_recorder` | `RosBagRecorder` | Context property retained; no singleton migration planned |
| `settingsManager` | `settings_manager` | `SettingsManager` | Context property retained; no singleton migration planned |

### Removed Aliases
| Identifier | Status |
|---|---|
| `baseStreamer` | Removed in Task 0.3; QML now targets `backend` where needed |
| `videoStreamer` | Removed in Task 0.3; QML now uses `baseStreamHandler` |

---

## Registration Pattern

All Python objects are exposed to QML via `setContextProperty()`:

```python
# In application.py — register all objects BEFORE engine.load()
ctx = engine.rootContext()
ctx.setContextProperty("stateStore", state_store)
ctx.setContextProperty("wheelController", bundle.wheel_controller)
ctx.setContextProperty("settingsManager", settings_manager)
# ... etc
```

> **⚠️ DO NOT use `qmlRegisterSingletonInstance()`** — broken in PySide6. See KNOWLEDGE.md.

QML access uses lowercase instance names directly (no import needed):
```qml
// Context property — available globally
Text { text: wheelController.left_wheel_speed }
Text { text: stateStore.control_mode }
```

---

## Signal-Based Bridge (QtBridge → QML)

All `findChild()` calls have been eliminated. `QtBridge` now communicates with QML via signals consumed by a `Connections` block in `MainWindow.qml`:

```python
# In qt_bridge.py — signals
showPopupRequested = Signal(str, str, str, int)    # title, message, type, delay
closePopupRequested = Signal()                      # close popup
toggleSidebarRequested = Signal()                   # toggle sidebar
toggleVideoOverlayRequested = Signal(bool, str)     # active, videoSource
updateVideoSourceRequested = Signal(str)            # videoSource
```

```qml
// In MainWindow.qml
Connections {
    target: backend
    function onShowPopupRequested(title, message, popupType, delay) { ... }
    function onClosePopupRequested() { messagePopup.close() }
    function onToggleSidebarRequested() { selectBar.toggleSidebar() }
    function onToggleVideoOverlayRequested(active, videoSource) { ... }
    function onUpdateVideoSourceRequested(videoSource) { ... }
}
```

**Remaining QML object access**: `engine.rootObjects()[0]` in `toggle_multiscreen_window()` via `QMetaObject.invokeMethod`.

**`input.py`**: Uses `close_popup_fn` callable (injected via constructor → `qt_bridge.close_popup`) instead of `findChild`.

---

## QML File Structure

Location: `python/paint_controller/qml/`

```
qml/
├── core/
│   ├── MainWindow.qml          # Root window, screen manager
│   └── CommonStyle.qml         # Shared styling (pragma Singleton)
├── navigation/
│   ├── SelectBar.qml           # Left sidebar
│   └── TopBar.qml              # Top status bar
├── pages/
│   ├── home/
│   │   ├── PageHome.qml
│   │   └── PageLauncher.qml
│   ├── spray/     → uses backend signals
│   ├── wheel/     → binds to wheelController
│   ├── winch/
│   ├── settings/  → camera, arm, wheels, main settings
│   ├── status/    → monitor & sensor displays
│   ├── tuning/
│   └── misc/
├── overlays/
│   ├── OverlayLayer.qml        # Overlay container
│   ├── video/
│   │   ├── VideoFullscreenOverlay.qml
│   │   └── components/
│   │       ├── BaseFrontOverlay.qml
│   │       ├── BaseTopViewSettingsPopup.qml
│   │       ├── WallDetectionOverlay.qml
│   │       └── ControlInfoPanel.qml
│   ├── lidar/
│   │   ├── LidarOverlay.qml
│   │   ├── Lidar2DView.qml
│   │   └── Lidar3DView.qml
│   ├── systemcontrol/
│   │   ├── SystemControlMenu.qml
│   │   ├── WorkFlowTab.qml
│   │   ├── SettingsTab.qml
│   │   ├── DeviceControlTab.qml
│   │   └── EditWorkFlowTab.qml
│   ├── EmergencyOverlay.qml
│   └── MultiScreenListUI.qml
├── components/
│   ├── buttons/
│   │   ├── ActionButton.qml
│   │   ├── CustomButton.qml
│   │   ├── NumpadButton.qml
│   │   ├── TouchSwitch.qml
│   │   └── MoveLengthButton.qml    → calls backend methods
│   ├── inputs/
│   │   ├── SettingInputField.qml
│   │   ├── KeyboardPopup.qml
│   │   └── Numpad variants
│   ├── displays/
│   │   ├── IndustrialCard.qml
│   │   ├── WheelsCard.qml          → reads wheelController properties
│   │   ├── ValvesCard.qml
│   │   ├── BatteryDisplay.qml
│   │   ├── LineGraph.qml
│   │   └── ... (14+ display components)
│   ├── panels/
│   │   ├── ControlPanel.qml
│   │   ├── ConnectionStatusPanel.qml
│   │   └── SettingsSection.qml
│   ├── popups/
│   │   └── CustomPopup.qml
│   └── specialized/
│       └── pointcloud/
│           ├── PointCloudGeometry.qml
│           └── PointCloudEffect.qml
```

### qmldir State
`qmldir` coverage is now in place across the QML tree.

Existing/special cases:
- `core/qmldir` — `singleton CommonStyle 1.0 CommonStyle.qml`
- `overlays/systemcontrol/qmldir` — pre-existing

Added during Task 1.9:
- `navigation/`
- `components/buttons/`, `components/displays/`, `components/inputs/`, `components/panels/`, `components/popups/`, `components/specialized/pointcloud/`
- `overlays/`, `overlays/lidar/`, `overlays/video/`, `overlays/video/components/`
- `pages/home/`, `pages/misc/`, `pages/settings/`, `pages/settings/components/`, `pages/settings/pages/`, `pages/spray/`, `pages/status/`, `pages/status/components/`, `pages/tuning/`, `pages/wheel/`, `pages/winch/`

The current rollout is intentionally conservative: these files provide type export entries only. The runtime still uses relative imports (for example `import "../pages/home"`) and does not yet depend on dotted URI-module imports. That avoids reintroducing the import/type-system instability that previously blocked singleton-registration work.

**Guardrail**: Never use bare `module PaintController` in any `qmldir`. If URI-module imports are introduced later, they need their own audited migration pass.

---

## Signal Connections (QML ← Python)

### Connections Pattern Used
```qml
Connections {
    target: backend / overlayController / wheelController / etc.
    function onSignalName(args) { /* handler */ }
}
```

### Key Signals

**Backend (`QtBridge`)**
- `showPopupRequested(title, message, popupType, delay)` → popup display in `MainWindow.qml`
- `closePopupRequested()` → popup close in `MainWindow.qml`
- `toggleSidebarRequested()` → `SelectBar.qml`
- `toggleVideoOverlayRequested(active, videoSource)` → fullscreen video overlay
- `updateVideoSourceRequested(videoSource)` → fullscreen source refresh

**OverlayController** (Dual joystick menu)
- `leftSelectedIndexChanged(int)`
- `rightSelectedIndexChanged(int)`
- `overlayChanged(bool)`
- `controlOptionsChanged(list)`
- `activeMenuChanged(str)`

**WheelController**
- `left_wheel_speed`, `right_wheel_speed` (Property signals)
- `left_wheel_position`, `right_wheel_position`
- `left_motor_available`, `right_motor_available`
- `enabled_changed(bool)`

**ScreenManager**
- `screens_changed()` → MainWindow.qml detects multi-screen connections

**EmergencyButtonHandler**
- `overlay_changed(bool, float, float)` → EmergencyOverlay.qml

---

## Python Property Bindings (@Property Decorator)

All exposed Python properties use `@Property(type, notify=signal)`:

### OverlayController (`ui/overlay.py:56-75`)
```python
@Property(list, notify=controlOptionsChanged)
def control_options(self): ...

@Property(int, notify=leftSelectedIndexChanged)
def left_selected_index(self): ...

@Property(bool, notify=overlayChanged)
def show_overlay(self): ...

@Property(str, notify=activeMenuChanged)
def active_menu(self): ...
```

### WheelController
```python
@Property(float, notify=left_wheel_speed_changed)
def left_wheel_speed(self): ...

@Property(float, notify=right_wheel_speed_changed)
def right_wheel_speed(self): ...
```

---

## Python Slots in QML (@Slot Decorator)

QML calls Python methods via `@Slot()` decorators:

### Common Slots

**WheelController**: `setEnabled(bool)`, `resetWheelPosition()`

**TeensyController**: `extendArm(length)`, `moveWinchIncrement(distance, speed)`

**OverlayController**: `toggle_system_menu()`, `toggle_left_menu()`, `toggle_right_menu()`, `move_up()`, `move_down()`, `set_joystick_controls(left, right)`

**BaseTopViewController**: `resetToDefaults()`

```qml
onClicked: wheelController.setEnabled(!wheelController.enabled)
onClicked: overlayController.toggle_system_menu()
```

---

## Python → QML Direct Access (Current State)

The live Python runtime no longer uses `findChild()` to reach QML objects.

- `QtBridge` uses signals consumed by a `Connections { target: backend }` block in `MainWindow.qml`
- `input.py` closes the popup through the injected `close_popup_fn` callable
- The old `QmlObjectName` enum was deleted
- `messagePopup`, `selectBar`, and `videoFullscreenOverlay` are no longer Python bridge contracts

**Only remaining imperative QML access**
- `engine.rootObjects()[0]` in `toggle_multiscreen_window()` via `QMetaObject.invokeMethod`

---

## C++ Paint Controller Bindings (DELETED — Phase 1A)

**Location**: ~~`src/paint_controller.cpp`~~ (deleted)

Source files (`src/*.cpp`, `include/paint_controller/*.hpp`) were deleted in Phase 1A. For historical context: the C++ path set only 2 of the 22 runtime context properties (`backend`, `baseStreamer`) and used `findChild` directly. See Section 7 of [02_ARCHITECTURE.md](02_ARCHITECTURE.md).

---

## Current Registration Pattern Summary

### What's Currently Used
- ✅ `setContextProperty()` for all runtime objects
- ✅ `@Property(type, notify=signal)` for bindable attributes
- ✅ `@Slot()` for QML-callable methods
- ✅ `Connections { target: obj }` for signal listening in QML
- ✅ Image providers for video streams
- ✅ Signal-based bridge for popup/sidebar/video overlay control
- ✅ Limited `objectName` usage for QML-side structure only
- ✅ One remaining root-object invocation for multiscreen window handling

### What's Being Migrated To
- ✅ `qmldir` manifests for module organization
- ✅ `required property` for explicit dependencies
- ✅ Versionless Qt6 imports (`import QtQuick` not `import QtQuick 2.15`)
- ❌ NOT using `qmlRegisterSingletonInstance()` (broken in PySide6 — see KNOWLEDGE.md)
- ❌ NOT using `@QmlElement` or `@QmlSingleton` (Audit R1 — incompatible with factory pattern)
- ❌ NOT using `QML_IMPORT_NAME` module variables
