# Paint Controller Architecture

This document provides a comprehensive overview of the Paint Controller's architecture, design patterns, and internal structure.

## Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [System Architecture](#system-architecture)
- [Package Structure](#package-structure)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Threading Model](#threading-model)
- [Communication Patterns](#communication-patterns)
- [UI Architecture](#ui-architecture)
- [Extension Points](#extension-points)

## Overview

The Paint Controller is built on a modular, event-driven architecture that combines ROS 2 for robot communication with Qt/QML for the user interface. The system follows the Model-View-Controller (MVC) pattern with additional service and handler layers for specialized functionality.

### Key Architectural Decisions

1. **ROS 2 Integration**: Separate thread for ROS 2 execution to prevent blocking the GUI
2. **Qt Signals/Slots**: Event-driven communication between components
3. **Modular Controllers**: Hardware-specific controllers with standardized interfaces
4. **YAML Workflows**: Declarative automation without code changes
5. **QML UI**: Separation of presentation from business logic

## Design Principles

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- **Controllers**: Hardware communication
- **Handlers**: Event processing and input management
- **Services**: High-level functionality (video, workflows)
- **Core**: Application lifecycle and coordination

### 2. Loose Coupling
Components communicate through:
- Qt Signals/Slots
- ROS 2 Topics/Services
- Shared configuration

This allows components to be replaced or upgraded independently.

### 3. Qt Integration
All components that interact with the GUI inherit from `QObject`:
- Enables signal/slot mechanism
- Provides property binding for QML
- Thread-safe UI updates via Qt's event system

### 4. Thread Safety
- ROS 2 runs in a dedicated thread (`RosThread`)
- Qt event loop runs in the main thread
- Cross-thread communication uses Qt's queued connections
- Hardware access is protected by mutexes where needed

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         QML User Interface                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Pages   │  │Components│  │ Overlays │  │ Widgets  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │   Qt Property Bindings    │
        └─────────────┬─────────────┘
                      │
┌─────────────────────┴─────────────────────────────────────────────┐
│                    RobotController (Main Application)              │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Core Management                          │  │
│  │  • Settings Manager                                         │  │
│  │  • Configuration Loader                                     │  │
│  │  • ROS Thread Management                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────┬──────────────┬─────────────┬─────────────────┐  │
│  │ Controllers │   Handlers   │  Services   │   UI/Widgets    │  │
│  ├─────────────┼──────────────┼─────────────┼─────────────────┤  │
│  │ • Lidar     │ • Steam Deck │ • Video     │ • Overlay       │  │
│  │ • Wheel     │ • Emergency  │ • Workflow  │ • VTK Widget    │  │
│  │ • Winch     │ • Heartbeat  │ • Screen    │                 │  │
│  │ • Teensy    │ • Input      │   Recorder  │                 │  │
│  │ • Wind      │ • Control    │             │                 │  │
│  │ • SSH       │   Processor  │             │                 │  │
│  │ • System    │ • Warnings   │             │                 │  │
│  └─────────────┴──────────────┴─────────────┴─────────────────┘  │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                          │
        ┌───────┴────────┐        ┌───────┴────────┐
        │  ROS 2 Thread  │        │  Qt Event Loop │
        │                │        │  (Main Thread) │
        └───────┬────────┘        └────────────────┘
                │
    ┌───────────┴───────────┐
    │   ROS 2 Middleware    │
    ├───────────────────────┤
    │ • Publishers          │
    │ • Subscribers         │
    │ • Services            │
    │ • Actions             │
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │   Robot Hardware      │
    │ • Motors/Actuators    │
    │ • Sensors             │
    │ • Controllers         │
    └───────────────────────┘
```

## Package Structure

### Directory Layout

```
python/paint_controller/
├── __init__.py              # Package initialization and exports
├── __main__.py              # Module entry point
│
├── core/                    # Core application components
│   ├── application.py       # Main RobotController and ROS integration
│   └── settings.py          # Settings management
│
├── controllers/             # Hardware-specific controllers
│   ├── lidar.py            # LiDAR sensor interface
│   ├── wheel.py            # Wheel/locomotion control
│   ├── winch.py            # Winch positioning system
│   ├── teensy.py           # Teensy microcontroller interface
│   ├── wind_monitor.py     # Wind sensor monitoring
│   ├── system_monitor.py   # System resource monitoring
│   └── ssh.py              # SSH connection management
│
├── handlers/                # Event and input handlers
│   ├── steam_deck.py       # Steam Deck controller input
│   ├── emergency.py        # Emergency stop handler
│   ├── heartbeat.py        # Device heartbeat monitoring
│   ├── input.py            # Generic input handling
│   ├── control_processor.py # Control signal processing
│   └── warnings.py         # Warning/alert management
│
├── services/                # Service modules
│   ├── video_stream.py     # Video streaming (GStreamer)
│   ├── screen_recorder.py  # Screen recording functionality
│   ├── workflow_legacy.py  # Legacy workflow system
│   └── workflow/           # Modern workflow system
│       ├── workflow_runner.py   # Workflow execution engine
│       ├── workflow_executor.py # Action execution
│       ├── scheduler.py         # Time-based scheduling
│       ├── actions.py           # Action definitions
│       └── hardware.py          # Hardware abstraction
│
├── ui/                      # UI controllers
│   └── overlay.py          # Overlay management
│
├── widgets/                 # Custom Qt widgets
│   └── vtk_pointcloud.py   # VTK 3D point cloud visualization
│
├── models/                  # Data models
│   └── action_config.py    # Action configuration models
│
├── scripts/                 # Standalone scripts
│   ├── steam_input_test.py
│   ├── test_vtk.py
│   └── test_vtk_ros.py
│
├── qml/                     # QML UI files
│   ├── core/               # Core QML components
│   ├── components/         # Reusable UI components
│   ├── pages/              # Application pages
│   ├── overlays/           # Overlay definitions
│   ├── widgets/            # Custom QML widgets
│   └── navigation/         # Navigation components
│
├── resource/                # Application resources
│   └── workflows/          # YAML workflow definitions
│
└── config/                  # Configuration files
    └── ssh_config.json     # SSH connections
```

### Module Dependencies

```
Core (application.py)
├── Controllers (all hardware controllers)
├── Handlers (all event handlers)
├── Services (video, workflow, etc.)
├── UI (overlays, widgets)
└── Models (configuration, data)

Each module is relatively independent, communicating through:
- Qt Signals/Slots
- ROS 2 Topics
- Shared configuration
```

## Core Components

### 1. RobotController (core/application.py)

The main application class that coordinates all components.

**Responsibilities:**
- Initialize ROS 2 node
- Create and manage all controllers, handlers, and services
- Load configuration and settings
- Manage application lifecycle
- Coordinate between ROS 2 and Qt threads

**Key Methods:**
```python
def __init__(self):
    # Initialize ROS 2 node
    # Create controllers
    # Setup handlers
    # Initialize services
    # Load QML UI

def _setup_controllers(self):
    # Create hardware controllers
    # Register with QML context

def _setup_handlers(self):
    # Create event handlers
    # Connect signals

def spin_ros(self):
    # ROS 2 event loop (runs in separate thread)
```

### 2. RosThread (core/application.py)

A QThread subclass that runs the ROS 2 executor.

**Purpose:**
- Keep ROS 2 spinning without blocking the GUI
- Enable callback processing in background
- Thread-safe shutdown

**Implementation:**
```python
class RosThread(QThread):
    def run(self):
        while rclpy.ok() and not self._stop_event.is_set():
            rclpy.spin_once(self.node, timeout_sec=0.1)
```

### 3. Controllers (controllers/)

Hardware-specific controllers that interface with robot components.

**Common Pattern:**
```python
class HardwareController(QObject):
    # Qt signals for state changes
    state_changed = Signal()
    
    def __init__(self, robot_controller: Node):
        super().__init__()
        self._robot_controller = robot_controller
        self._property = initial_value
        self._setup_ros()
    
    def _setup_ros(self):
        # Create publishers/subscribers
        # Register callbacks
        pass
    
    @Property(type, notify=state_changed)
    def property(self):
        return self._property
    
    @property.setter
    def property(self, value):
        if self._property != value:
            self._property = value
            self.state_changed.emit()
```

**Examples:**

- **WinchController**: Controls cable winch position and speed
- **WheelController**: Manages wheel/locomotion movement
- **LidarController**: Receives and processes LiDAR data
- **TeensyController**: Interfaces with Teensy microcontroller
- **SystemMonitor**: Monitors system resources (CPU, memory, etc.)

### 4. Handlers (handlers/)

Event processors and input managers.

**Key Handlers:**

#### SteamDeckHandler
- Reads HID input from Steam Deck controller
- Processes buttons, joysticks, triggers, IMU
- Emits Qt signals for button presses
- Runs reader thread for continuous input

#### EmergencyButtonHandler
- Monitors emergency stop conditions
- Publishes emergency stop commands
- Manages emergency state visualization

#### HeartbeatHandler
- Monitors device connectivity
- Sends periodic heartbeat messages
- Tracks device status
- Triggers warnings on timeout

#### ControlProcessor
- Processes joystick input
- Applies dead zones and scaling
- Publishes control commands (velocity, position)
- Manages control modes (Base/EF)

### 5. Services (services/)

High-level functionality modules.

#### VideoStreamHandler
- Manages multiple camera streams
- GStreamer pipeline management
- Provides QML image providers
- Handles stream start/stop/reconnect

#### WorkFlowRunner
- Loads YAML workflow definitions
- Executes action sequences
- Manages parallel and sequential actions
- Provides progress feedback

#### ScreenRecorder
- Records application screen
- GStreamer-based recording
- Start/stop/save functionality

### 6. UI Components (ui/, widgets/)

#### OverlayController
- Manages overlay visibility and state
- Controls overlay animations
- Provides overlay data to QML

#### VTKPointCloudWidget
- Embeds VTK rendering in Qt
- Displays 3D point cloud data
- Interactive visualization controls

## Data Flow

### Control Flow Example: Joystick Input to Robot Motion

```
1. Steam Deck Controller (Hardware)
   │
   ↓
2. SteamDeckHandler.reader_thread reads HID data
   │
   ↓
3. SteamDeckHandler processes and emits Qt signals
   │
   ↓
4. ControlProcessor receives joystick signals
   │
   ↓
5. ControlProcessor applies dead zones, scaling
   │
   ↓
6. ControlProcessor publishes ROS 2 Twist message
   │
   ↓
7. ROS 2 Middleware (RosThread)
   │
   ↓
8. Robot Hardware receives commands
```

### Data Flow Example: Sensor Data to GUI

```
1. Robot Hardware (Sensor)
   │
   ↓
2. ROS 2 publishes sensor data
   │
   ↓
3. RosThread receives message
   │
   ↓
4. Controller callback processes data
   │
   ↓
5. Controller updates internal state
   │
   ↓
6. Controller emits Qt signal (property changed)
   │
   ↓
7. QML binding updates automatically
   │
   ↓
8. GUI displays updated value
```

## Threading Model

### Main Thread (Qt Event Loop)
- GUI rendering and event processing
- Qt signal/slot execution
- QML property binding updates
- User interaction handling

### ROS Thread (RosThread)
- ROS 2 executor (rclpy.spin)
- Callback processing
- Message publishing/receiving
- Service calls

### Worker Threads
- **SteamDeckReaderThread**: Continuous HID device reading
- **SystemMonitorWorker**: System resource monitoring
- **VideoStream threads**: GStreamer pipeline processing

### Thread Communication

```python
# From ROS thread to Main thread
# Use Qt's thread-safe signal emission
self.signal.emit(data)  # Automatically queued to main thread

# From Main thread to ROS thread
# Use thread-safe publishers (rclpy is thread-safe for publishing)
self.publisher.publish(msg)

# Between worker threads and main thread
# Always use Qt signals/slots
```

## Communication Patterns

### 1. ROS 2 Topics

**Publishers:**
```python
# In controller __init__
self._cmd_vel_pub = robot_controller.create_publisher(
    Twist, '/cmd_vel', 10
)

# When publishing
msg = Twist()
msg.linear.x = velocity
self._cmd_vel_pub.publish(msg)
```

**Subscribers:**
```python
# In controller __init__
self._state_sub = robot_controller.create_subscription(
    RobotState, '/robot/state', self._state_callback, 10
)

# Callback
def _state_callback(self, msg):
    self.set_state(msg.state)  # Updates property, emits signal
```

### 2. Qt Signals/Slots

**Defining Signals:**
```python
class MyController(QObject):
    value_changed = Signal(float)
    
    def set_value(self, val):
        self._value = val
        self.value_changed.emit(val)
```

**Connecting Signals:**
```python
controller.value_changed.connect(self.on_value_changed)
```

**Property Binding for QML:**
```python
@Property(float, notify=value_changed)
def value(self):
    return self._value
```

### 3. QML Property Binding

```qml
// QML automatically updates when property changes
Text {
    text: robotController.winchController.position
}
```

## UI Architecture

### QML Structure

The UI is built with QtQuick/QML and follows a component-based architecture.

#### Main Window
```
ApplicationWindow (main.qml)
├── Navigation Bar
├── Content Stack
│   ├── Home Page
│   ├── Control Page
│   ├── Monitoring Page
│   └── Settings Page
├── Overlays
│   ├── Emergency Overlay
│   ├── Warning Overlay
│   └── Info Overlay
└── Status Bar
```

#### Component Organization

**Pages** (`qml/pages/`):
- Full-screen views
- Main application sections
- Page-specific logic

**Components** (`qml/components/`):
- Reusable UI elements
- Buttons, cards, panels
- Stateless when possible

**Widgets** (`qml/widgets/`):
- Complex, stateful components
- Custom visualizations
- Embedded native widgets (VTK)

**Overlays** (`qml/overlays/`):
- Modal or semi-modal views
- Temporary notifications
- Emergency displays

### QML ↔ Python Integration

#### Exposing Python Objects to QML

```python
# In RobotController.__init__
engine = QQmlApplicationEngine()
context = engine.rootContext()

# Make controller available to QML
context.setContextProperty("robotController", self)
context.setContextProperty("winchController", self.winch_controller)
```

#### Using in QML

```qml
Item {
    // Access properties
    text: winchController.position
    
    // Call methods
    onClicked: robotController.emergencyStop()
    
    // Connect to signals
    Connections {
        target: winchController
        function onPositionChanged() {
            console.log("Position updated")
        }
    }
}
```

## Extension Points

### Adding a New Hardware Controller

1. **Create controller file** in `controllers/`:
```python
from PySide6.QtCore import QObject, Signal, Property

class MyController(QObject):
    value_changed = Signal()
    
    def __init__(self, robot_controller):
        super().__init__()
        self._robot_controller = robot_controller
        self._value = 0.0
        self._setup_ros()
    
    def _setup_ros(self):
        self._sub = self._robot_controller.create_subscription(
            MyMsg, '/my/topic', self._callback, 10
        )
    
    def _callback(self, msg):
        self.value = msg.value
    
    @Property(float, notify=value_changed)
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        if self._value != v:
            self._value = v
            self.value_changed.emit()
```

2. **Register in RobotController**:
```python
# In application.py, _setup_controllers()
self.my_controller = MyController(self)
self._qml_engine.rootContext().setContextProperty(
    "myController", self.my_controller
)
```

3. **Use in QML**:
```qml
Text {
    text: "Value: " + myController.value
}
```

### Adding a New Workflow Action

1. **Define action in `services/workflow/actions.py`**:
```python
def execute_my_action(hardware, params):
    """Execute custom action"""
    value = params.get('value', 0)
    hardware.my_controller.do_something(value)
```

2. **Register action in workflow executor**

3. **Use in YAML workflow**:
```yaml
actions:
  - id: my_action
    type: my_action
    params:
      value: 42
```

### Adding a New QML Page

1. **Create page file** in `qml/pages/MyPage.qml`
2. **Add navigation** in main QML
3. **Access controllers** via context properties

## Best Practices

### For Controllers
- Inherit from `QObject`
- Define signals for all state changes
- Use `@Property` decorator for QML-accessible properties
- Keep ROS-specific code isolated in `_setup_ros()` methods
- Document all public methods and properties

### For Handlers
- Process events, don't store state (when possible)
- Emit signals for state changes
- Use Qt's thread-safe signal mechanism for cross-thread communication

### For Services
- Provide high-level, stateful functionality
- Abstract implementation details
- Use clear, documented interfaces

### For QML
- Keep business logic in Python
- Use property bindings for reactive updates
- Componentize reusable UI elements
- Follow Qt Quick best practices

### Thread Safety
- Never call GUI functions from ROS callbacks directly
- Always emit signals from ROS callbacks, handle in main thread
- Use Qt's queued connections for cross-thread signals
- Protect shared data with mutexes if needed

## Conclusion

The Paint Controller architecture is designed for:
- **Modularity**: Easy to add/remove/replace components
- **Maintainability**: Clear separation of concerns
- **Extensibility**: Well-defined extension points
- **Safety**: Thread-safe by design
- **Usability**: Reactive UI with immediate feedback

Understanding this architecture will help you navigate the codebase, add features, and maintain the system effectively.
