# QML ↔ Python Bindings Inventory

> **Source**: Codebase review (2026-04). Updated with audit findings.
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

# Register singletons / set context properties BEFORE load
qml_path = os.path.join(qml_dir, 'core', 'MainWindow.qml')
engine.load(QUrl.fromLocalFile(qml_path))
```

---

## Current Runtime Registration State

As of 2026-04-17, runtime registration is **hybrid**:

- `StateStore` is already registered with `qmlRegisterSingletonInstance()` as `PaintController 1.0 / StateStore`
- 23 remaining runtime identifiers are still exposed through `engine.rootContext().setContextProperty()`
- Removed aliases `baseStreamer` and `videoStreamer` are no longer part of the live Python/QML path

### Singleton-Registered
| QML Name | Source | Type | Completed Task |
|---|---|---|---|
| `StateStore` | `state_store` | `StateStore` | `1.0` |

### Core Objects
| Property Name | Source | Type | Migration Task |
|---|---|---|---|
| `backend` | `qt_bridge` | `QtBridge` | Task 1.2 |
| `overlayController` | `bundle.overlay_controller` | `OverlayController` | Task 1.3 |
| `controlProcessor` | `bundle.control_processor` | `ControlProcessor` | Task 1.3 |

### Hardware Controllers
| Property Name | Source | Type | Migration Task |
|---|---|---|---|
| `wheelController` | `bundle.wheel_controller` | `WheelController` | Task 1.4 |
| `winchController` | `bundle.winch_controller` | `WinchController` | Task 1.6 |
| `teensyController` | `bundle.teensy_controller` | `TeensyController` | Task 1.5 |
| `esp32ValveController` | `bundle.esp32_valve_controller` | `ESP32ValveController` | Task 1.7a |
| `lidarController` | `bundle.lidar_controller` | `LidarController` | Task 1.7a |
| `windMonitor` | `bundle.wind_monitor` | `WindMonitor` | Task 1.3 |

### Services
| Property Name | Source | Type | Migration Task |
|---|---|---|---|
| `workFlowHandler` | `bundle.workflow_handler` | `WorkFlowHandler` | Task 1.8 |
| `workFlowRunner` | `bundle.workflow_runner` | `WorkFlowRunner` | Task 1.8 |
| `baseStreamHandler` | `video_stream_handler` | `VideoStreamHandler` | Task 1.7a |
| `baseTopViewController` | `base_top_view_service` | `BaseTopViewService` | Task 1.7a |

### System & UI
| Property Name | Source | Type | Migration Task |
|---|---|---|---|
| `warningHandler` | `bundle.warning_handler` | `WarningHandler` | Task 1.3 |
| `heartbeatHandler` | `bundle.heartbeat_handler` | `UIHeartbeatHandler` | Task 1.3 |
| `sshHandler` | `bundle.ssh_controller` | `UISSHController` | Task 1.7a |
| `systemMonitor` | `bundle.system_monitor` | `SystemMonitor` | Task 1.3 |
| `screenManager` | `bundle.screen_manager` | `ScreenManager` | Task 1.7b |
| `screenRecorder` | `bundle.screen_recorder` | `ScreenRecorder` | Task 1.7b |
| `rosBagRecorder` | `bundle.ros_bag_recorder` | `RosBagRecorder` | Task 1.7b |
| `settingsManager` | `settings_manager` | `SettingsManager` | Task 1.1 |
| `actionConfig` | `bundle.action_config` | `ActionConfigPython` | Task 1.7b |

### Removed Aliases
| Identifier | Status |
|---|---|
| `baseStreamer` | Removed in Task 0.3; QML now targets `backend` where needed |
| `videoStreamer` | Removed in Task 0.3; QML now uses `baseStreamHandler` |

---

## Registration Target Pattern

After migration, every context property becomes a singleton:

```python
# In application.py — replaces setContextProperty block
from PySide6.QtQml import qmlRegisterSingletonInstance

qmlRegisterSingletonInstance(
    WheelController,           # type
    "PaintController",         # URI  
    1, 0,                      # version major.minor
    "WheelController",         # QML name
    wheel_controller_instance  # object
)
```

**CRITICAL (Audit R1)**: Do NOT add `QML_IMPORT_NAME` or `QML_IMPORT_MAJOR_VERSION` module variables. Those are only for `@QmlElement` decorator — they are dead code when using `qmlRegisterSingletonInstance()`.

QML access changes from:
```qml
// OLD — global context property
Text { text: wheelController.left_wheel_speed }

// NEW — explicit import
import PaintController 1.0
Text { text: WheelController.left_wheel_speed }
```

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
│   │       ├── PointEditorOverlay.qml
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
└── widgets/
    └── actions/
        ├── ActionSequence.qml
        ├── ActionItem.qml
        └── SequenceList.qml
```

### qmldir State
One `qmldir` already exists under `overlays/systemcontrol/`. The rest of the QML tree still uses relative imports (e.g., `import "../pages/home"`).

**Task 1.9** creates `qmldir` for each directory.  
**CRITICAL (Audit R8)**: Must use dotted names like `PaintController.Core`, NOT bare `module PaintController` (namespace collision with singleton URI).

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
- `emergency_overlay_changed(visible, current_duration, target_duration)` → EmergencyOverlay.qml
- `frame_ready()` → PageSpray.qml
- UI toggle methods remain imperative bridge methods until Task 1.2 removes the remaining `findChild()` calls

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

## findChild() Lookups (Python → QML) — CURRENT LIVE DEBT

### Current Locations (5 total — Audit R3 found the 5th)

| Location | objectName | What it does |
|---|---|---|
| `core/qt_bridge.py` | `messagePopup` | Show popup |
| `core/qt_bridge.py` | `selectBar` | Toggle sidebar |
| `core/qt_bridge.py` | `videoFullscreenOverlay` | Toggle fullscreen video |
| `core/qt_bridge.py` | `videoFullscreenOverlay` | Update fullscreen source |
| `handlers/input.py` | `messagePopup` | Close popup before mode switch |

### objectName Enum
```python
# utils/constants.py:39-42
class QmlObjectName(str, Enum):
    MESSAGE_POPUP = "messagePopup"
    SELECT_BAR = "selectBar"
    VIDEO_FULLSCREEN_OVERLAY = "videoFullscreenOverlay"
```

### objectName Declarations in QML

| QML Location | objectName | Keep/Remove after migration |
|---|---|---|
| `MainWindow.qml:80` | `selectBar` | **REMOVE** — replaced by `navigateToPageRequested` signal |
| `MainWindow.qml:135` | `stackView` | **KEEP** — used by QML/JS navigation code |
| `MainWindow.qml:225` | `messagePopup` | **REMOVE** — replaced by `showPopupRequested`/`closePopupRequested` signals |
| `MainWindow.qml:248` | `videoFullscreenOverlay` | **REMOVE** — replaced by `toggleVideoOverlayRequested` signal |
| `MainWindow.qml:256` | `lidarOverlay` | **KEEP** — used by QML internally |

### Replacement Signals (Task 1.2)

Planned for `QtBridge(QObject)` in Task 1.2:

| Signal | Replaces | Emitted from |
|---|---|---|
| `showPopupRequested(str, str, str)` | `findChild("messagePopup").show()` | `application.py` |
| `closePopupRequested()` | `findChild("messagePopup").close()` | `application.py` + `input.py` |
| `navigateToPageRequested(str)` | `findChild("selectBar").setCurrentIndex()` | `application.py` |
| `toggleVideoOverlayRequested(bool)` | `findChild("videoFullscreenOverlay").toggleOverlay()` | `application.py` |

QML side:
```qml
Connections {
    target: QtBridge  // singleton after Task 1.2
    function onShowPopupRequested(title, message, type) { messagePopup.show(title, message, type) }
    function onClosePopupRequested() { messagePopup.close() }
    function onNavigateToPageRequested(page) { selectBar.navigateTo(page) }
    function onToggleVideoOverlayRequested(visible) { videoFullscreenOverlay.toggleOverlay(visible) }
}
```

---

## C++ Paint Controller Bindings (DEPRECATED)

**Location**: `src/paint_controller.cpp`

```cpp
// Only 2 of 26 context properties set
engine.rootContext()->setContextProperty("backend", controller.get());
engine.rootContext()->setContextProperty("baseStreamer", controller.get());

// Also uses findChild for same objects
QObject* select_bar = root->findChild<QObject*>("selectBar");
QObject* popup = root->findChild<QObject*>("messagePopup");
```

**Status**: Formally deprecated per user decision (Audit R2). Will break when `baseStreamer` is removed in Task 0.3. See deprecation notice in [01_MASTER_PLAN.md](01_MASTER_PLAN.md).

---

## Current Registration Pattern Summary

### What's Currently Used
- ✅ `qmlRegisterSingletonInstance()` for `StateStore`
- ✅ `setContextProperty()` for the remaining runtime objects (hybrid registration)
- ✅ `@Property(type, notify=signal)` for bindable attributes
- ✅ `@Slot()` for QML-callable methods
- ✅ `Connections { target: obj }` for signal listening in QML
- ✅ Image providers for video streams
- ✅ `findChild()` lookups for direct QML access (5 calls)
- ✅ `objectName` for component identification

### What's Being Migrated To
- ✅ `qmlRegisterSingletonInstance()` for all runtime objects over time
- ✅ QML `Connections {}` with signals replacing `findChild()`
- ✅ `qmldir` manifests for module organization
- ✅ `required property` for explicit dependencies
- ✅ Versionless Qt6 imports (`import QtQuick` not `import QtQuick 2.15`)
- ❌ NOT using `@QmlElement` or `@QmlSingleton` (Audit R1 — incompatible with factory pattern)
- ❌ NOT using `QML_IMPORT_NAME` module variables (dead code for `qmlRegisterSingletonInstance`)
