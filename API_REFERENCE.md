# API Reference

Complete API documentation for the Paint Controller Python package.

## Table of Contents

- [Core](#core)
  - [RobotController](#robotcontroller)
  - [SettingsManager](#settingsmanager)
- [Controllers](#controllers)
  - [LidarController](#lidarcontroller)
  - [WheelController](#wheelcontroller)
  - [WinchController](#winchcontroller)
  - [TeensyController](#teensycontroller)
  - [SystemMonitor](#systemmonitor)
- [Handlers](#handlers)
  - [SteamDeckHandler](#steamdeckhandler)
  - [EmergencyButtonHandler](#emergencybuttonhandler)
  - [HeartbeatHandler](#heartbeathandler)
  - [ControlProcessor](#controlprocessor)
- [Services](#services)
  - [VideoStreamHandler](#videostreamhandler)
  - [WorkFlowRunner](#workflowrunner)
  - [ScreenRecorder](#screenrecorder)
- [Models](#models)
- [Widgets](#widgets)

## Core

### RobotController

Main application controller that coordinates all components.

**Module**: `paint_controller.core.application`

#### Class: RobotController(Node)

Inherits from ROS 2 `Node` and serves as the central controller.

**Constructor:**
```python
RobotController(node_name: str = 'paint_controller')
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `lidar_controller` | LidarController | LiDAR sensor controller |
| `wheel_controller` | WheelController | Wheel/locomotion controller |
| `winch_controller` | WinchController | Winch control system |
| `teensy_controller` | TeensyController | Teensy microcontroller interface |
| `system_monitor` | SystemMonitor | System resource monitor |
| `steam_deck` | SteamDeckHandler | Steam Deck input handler |
| `video_handler` | VideoStreamHandler | Video streaming service |
| `workflow_runner` | WorkFlowRunner | Workflow execution engine |

**Signals:**
- `shutdownRequested`: Emitted when application shutdown is requested

**Methods:**

##### spin_ros()
```python
def spin_ros(self) -> None
```
Main ROS 2 event loop. Runs in separate thread.

**Example:**
```python
controller = RobotController()
ros_thread = RosThread(controller)
ros_thread.start()
```

##### emergency_stop()
```python
@Slot()
def emergency_stop(self) -> None
```
Trigger emergency stop for all systems.

**Example:**
```python
controller.emergency_stop()
```

##### shutdown()
```python
def shutdown(self) -> None
```
Gracefully shut down the application and all components.

---

### SettingsManager

Manages application settings and configuration.

**Module**: `paint_controller.core.settings`

#### Class: SettingsManager(QObject)

**Constructor:**
```python
SettingsManager(config_path: str = None)
```

**Parameters:**
- `config_path`: Path to configuration file (optional)

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `theme` | str | UI theme (light/dark) |
| `joystick_dead_zone` | float | Joystick dead zone (0.0-1.0) |
| `control_mode` | str | Control mode (base/ef) |

**Signals:**
- `settings_changed`: Emitted when settings are modified

**Methods:**

##### get_setting()
```python
def get_setting(self, key: str, default=None) -> Any
```
Get setting value.

**Parameters:**
- `key`: Setting key
- `default`: Default value if key doesn't exist

**Returns:** Setting value

##### set_setting()
```python
def set_setting(self, key: str, value: Any) -> None
```
Set setting value.

**Parameters:**
- `key`: Setting key
- `value`: Value to set

##### save()
```python
def save(self) -> bool
```
Save settings to disk.

**Returns:** True if successful

**Example:**
```python
settings = SettingsManager()
settings.set_setting('theme', 'dark')
settings.save()
```

---

## Controllers

### LidarController

Interface for LiDAR sensor data.

**Module**: `paint_controller.controllers.lidar`

#### Class: LidarController(QObject)

**Constructor:**
```python
LidarController(robot_controller: Node)
```

**Properties:**

| Property | Type | QML Accessible | Description |
|----------|------|----------------|-------------|
| `distance` | float | Yes | Distance to wall (mm) |
| `angle` | float | Yes | Angle to wall (degrees) |

**Signals:**
- `distance_changed`: Emitted when distance updates
- `angle_changed`: Emitted when angle updates

**ROS Topics:**

| Topic | Type | Direction |
|-------|------|-----------|
| `/ef/lidar/wall_detection/distance` | Float32 | Subscribe |
| `/ef/lidar/wall_detection/angle` | Float32 | Subscribe |

**Example:**
```python
lidar = LidarController(robot_controller)
lidar.distance_changed.connect(lambda: print(f"Distance: {lidar.distance}"))
```

**QML Usage:**
```qml
Text {
    text: "Distance: " + lidarController.distance + " mm"
}
```

---

### WheelController

Controls robot base locomotion.

**Module**: `paint_controller.controllers.wheel`

#### Class: WheelController(QObject)

**Constructor:**
```python
WheelController(robot_controller: Node)
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `linear_x` | float | Forward/backward velocity (m/s) |
| `linear_y` | float | Left/right velocity (m/s) |
| `angular_z` | float | Rotational velocity (rad/s) |
| `is_moving` | bool | Whether robot is moving |

**Signals:**
- `velocity_changed`: Emitted when velocity changes
- `is_moving_changed`: Emitted when movement state changes

**Methods:**

##### set_velocity()
```python
@Slot(float, float, float)
def set_velocity(self, linear_x: float, linear_y: float, angular_z: float) -> None
```
Set wheel velocity.

**Parameters:**
- `linear_x`: Forward velocity (m/s)
- `linear_y`: Strafe velocity (m/s)
- `angular_z`: Rotational velocity (rad/s)

##### stop()
```python
@Slot()
def stop(self) -> None
```
Stop all wheel movement.

**ROS Topics:**

| Topic | Type | Direction |
|-------|------|-----------|
| `/cmd_vel` | Twist | Publish |
| `/wheel/state` | WheelState | Subscribe |

**Example:**
```python
wheel = WheelController(robot_controller)
wheel.set_velocity(0.5, 0.0, 0.0)  # Move forward at 0.5 m/s
wheel.stop()
```

---

### WinchController

Controls winch positioning system.

**Module**: `paint_controller.controllers.winch`

#### Class: WinchController(QObject)

**Constructor:**
```python
WinchController(robot_controller: Node)
```

**Properties:**

| Property | Type | QML Accessible | Description |
|----------|------|----------------|-------------|
| `position` | float | Yes | Current position (mm) |
| `target_position` | float | Yes | Target position (mm) |
| `speed` | float | Yes | Current speed (mm/s) |
| `is_moving` | bool | Yes | Movement state |
| `is_homed` | bool | Yes | Homing state |

**Signals:**
- `position_changed`: Position updated
- `target_position_changed`: Target changed
- `speed_changed`: Speed updated
- `is_moving_changed`: Movement state changed
- `is_homed_changed`: Homing state changed

**Methods:**

##### move_absolute()
```python
@Slot(float, float)
def move_absolute(self, position: float, speed: float) -> None
```
Move to absolute position.

**Parameters:**
- `position`: Target position (mm)
- `speed`: Movement speed (mm/s)

##### move_relative()
```python
@Slot(float, float)
def move_relative(self, distance: float, speed: float) -> None
```
Move relative to current position.

**Parameters:**
- `distance`: Distance to move (mm, negative for up)
- `speed`: Movement speed (mm/s)

##### stop()
```python
@Slot()
def stop(self) -> None
```
Stop winch movement immediately.

##### home()
```python
@Slot()
def home(self) -> None
```
Execute homing sequence.

**ROS Topics:**

| Topic | Type | Direction |
|-------|------|-----------|
| `/winch/command` | WinchCommand | Publish |
| `/winch/state` | WinchState | Subscribe |

**Example:**
```python
winch = WinchController(robot_controller)

# Move to 5000mm at 150mm/s
winch.move_absolute(5000, 150)

# Move up 1000mm
winch.move_relative(-1000, 100)

# Emergency stop
winch.stop()
```

---

### TeensyController

Interface for Teensy microcontroller.

**Module**: `paint_controller.controllers.teensy`

#### Class: TeensyController(QObject)

**Constructor:**
```python
TeensyController(robot_controller: Node)
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `valve_states` | dict | Current valve states (id -> bool) |
| `sensor_values` | dict | Sensor readings (id -> float) |
| `is_connected` | bool | Connection status |

**Signals:**
- `valve_state_changed`: Valve state updated
- `sensor_value_changed`: Sensor reading updated
- `connection_changed`: Connection state changed

**Methods:**

##### set_valve()
```python
@Slot(int, bool)
def set_valve(self, valve_id: int, state: bool) -> None
```
Control valve state.

**Parameters:**
- `valve_id`: Valve identifier (0-n)
- `state`: True = open, False = close

##### get_valve_state()
```python
def get_valve_state(self, valve_id: int) -> bool
```
Get current valve state.

**Returns:** True if open, False if closed

**ROS Topics:**

| Topic | Type | Direction |
|-------|------|-----------|
| `/teensy/valve_command` | ValveCommand | Publish |
| `/teensy/valve_state` | ValveState | Subscribe |
| `/teensy/sensors` | SensorData | Subscribe |

**Example:**
```python
teensy = TeensyController(robot_controller)

# Open valve 1
teensy.set_valve(1, True)

# Close valve 1
teensy.set_valve(1, False)

# Check valve state
if teensy.get_valve_state(1):
    print("Valve 1 is open")
```

---

### SystemMonitor

Monitors system resources.

**Module**: `paint_controller.controllers.system_monitor`

#### Class: SystemMonitor(QObject)

**Constructor:**
```python
SystemMonitor()
```

**Properties:**

| Property | Type | QML Accessible | Description |
|----------|------|----------------|-------------|
| `cpu_usage` | float | Yes | CPU usage (0-100%) |
| `memory_usage` | float | Yes | Memory usage (0-100%) |
| `disk_usage` | float | Yes | Disk usage (0-100%) |
| `network_sent` | float | Yes | Network bytes sent |
| `network_received` | float | Yes | Network bytes received |
| `temperature` | float | Yes | CPU temperature (°C) |

**Signals:**
- `stats_updated`: Emitted when stats are updated (every 2 seconds)

**Methods:**

##### start()
```python
def start(self) -> None
```
Start monitoring.

##### stop()
```python
def stop(self) -> None
```
Stop monitoring.

**Example:**
```python
monitor = SystemMonitor()
monitor.stats_updated.connect(lambda: print(f"CPU: {monitor.cpu_usage}%"))
monitor.start()
```

---

## Handlers

### SteamDeckHandler

Handles Steam Deck controller input.

**Module**: `paint_controller.handlers.steam_deck`

#### Class: SteamDeckHandler(QObject)

**Constructor:**
```python
SteamDeckHandler()
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_connected` | bool | Controller connection state |
| `left_joystick_x` | float | Left joystick X (-1.0 to 1.0) |
| `left_joystick_y` | float | Left joystick Y (-1.0 to 1.0) |
| `right_joystick_x` | float | Right joystick X (-1.0 to 1.0) |
| `right_joystick_y` | float | Right joystick Y (-1.0 to 1.0) |
| `left_trigger` | float | Left trigger (0.0 to 1.0) |
| `right_trigger` | float | Right trigger (0.0 to 1.0) |

**Signals:**

Button signals:
- `button_pressed(int)`: Button was pressed (button ID)
- `button_released(int)`: Button was released (button ID)
- `a_pressed`, `b_pressed`, `x_pressed`, `y_pressed`: Face buttons
- `l4_pressed`, `r4_pressed`: Back buttons
- `steam_pressed`, `steam_released`: Steam button
- `menu_pressed`: Menu button

Joystick signals:
- `left_joystick_changed`: Left joystick moved
- `right_joystick_changed`: Right joystick moved

**Methods:**

##### start()
```python
def start(self) -> bool
```
Start reading from controller.

**Returns:** True if successful

##### stop()
```python
def stop(self) -> None
```
Stop reading from controller.

**Example:**
```python
steam_deck = SteamDeckHandler()

# Connect button signals
steam_deck.a_pressed.connect(lambda: print("A button pressed"))

# Connect joystick signals  
steam_deck.left_joystick_changed.connect(
    lambda: print(f"Left stick: {steam_deck.left_joystick_x}, {steam_deck.left_joystick_y}")
)

# Start reading
steam_deck.start()
```

---

### EmergencyButtonHandler

Handles emergency stop functionality.

**Module**: `paint_controller.handlers.emergency`

#### Class: EmergencyButtonHandler(QObject)

**Constructor:**
```python
EmergencyButtonHandler(robot_controller: Node)
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_emergency_active` | bool | Emergency state |

**Signals:**
- `emergency_activated`: Emergency stop triggered
- `emergency_cleared`: Emergency state cleared

**Methods:**

##### activate_emergency()
```python
@Slot()
def activate_emergency(self) -> None
```
Trigger emergency stop.

##### clear_emergency()
```python
@Slot()
def clear_emergency(self) -> None
```
Clear emergency state.

**ROS Topics:**

| Topic | Type | Direction |
|-------|------|-----------|
| `/emergency_stop` | Bool | Publish |

**Example:**
```python
emergency = EmergencyButtonHandler(robot_controller)
emergency.emergency_activated.connect(lambda: print("EMERGENCY STOP!"))
emergency.activate_emergency()
```

---

### HeartbeatHandler

Monitors device connectivity via heartbeats.

**Module**: `paint_controller.handlers.heartbeat`

#### Class: UIHeartbeatHandler(QObject)

**Constructor:**
```python
UIHeartbeatHandler(robot_controller: Node)
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `device_status` | dict | Device ID -> status dict |

**Signals:**
- `device_status_changed(str)`: Device status updated (device ID)
- `device_timeout(str)`: Device timed out (device ID)

**Methods:**

##### add_device()
```python
def add_device(self, device_id: str, timeout: float = 5.0) -> None
```
Add device to monitor.

**Parameters:**
- `device_id`: Unique device identifier
- `timeout`: Timeout in seconds

##### remove_device()
```python
def remove_device(self, device_id: str) -> None
```
Stop monitoring device.

##### get_device_status()
```python
def get_device_status(self, device_id: str) -> dict
```
Get device status.

**Returns:** Dict with keys: `is_alive`, `last_seen`, `timeout`

**Example:**
```python
heartbeat = UIHeartbeatHandler(robot_controller)

# Monitor a device
heartbeat.add_device("robot_pc", timeout=5.0)

# Check status
status = heartbeat.get_device_status("robot_pc")
if status['is_alive']:
    print("Device is connected")
```

---

### ControlProcessor

Processes control input and publishes commands.

**Module**: `paint_controller.handlers.control_processor`

#### Class: ControlProcessor(QObject)

**Constructor:**
```python
ControlProcessor(robot_controller: Node, config: ControlConfig)
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `control_mode` | str | Current mode ("base" or "ef") |
| `is_active` | bool | Control active state |

**Signals:**
- `control_mode_changed`: Mode was changed
- `is_active_changed`: Active state changed

**Methods:**

##### set_control_mode()
```python
@Slot(str)
def set_control_mode(self, mode: str) -> None
```
Set control mode.

**Parameters:**
- `mode`: "base" or "ef"

##### process_joystick()
```python
def process_joystick(self, x: float, y: float) -> tuple
```
Process joystick input with dead zone.

**Parameters:**
- `x`: X-axis value (-1.0 to 1.0)
- `y`: Y-axis value (-1.0 to 1.0)

**Returns:** Tuple of (processed_x, processed_y)

**Example:**
```python
config = ControlConfig(dead_zone=0.15)
processor = ControlProcessor(robot_controller, config)

# Set mode
processor.set_control_mode("base")

# Process input
x, y = processor.process_joystick(0.1, 0.8)  # Applies dead zone
```

---

## Services

### VideoStreamHandler

Manages video streaming from cameras.

**Module**: `paint_controller.services.video_stream`

#### Class: VideoStreamHandler(QObject)

**Constructor:**
```python
VideoStreamHandler()
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `streams` | list | Active camera streams |

**Signals:**
- `stream_started(str)`: Stream started (stream ID)
- `stream_stopped(str)`: Stream stopped (stream ID)
- `stream_error(str, str)`: Stream error (stream ID, error message)

**Methods:**

##### add_stream()
```python
def add_stream(self, stream_id: str, url: str, name: str = "") -> bool
```
Add video stream.

**Parameters:**
- `stream_id`: Unique stream identifier
- `url`: Stream URL (RTSP, HTTP, etc.)
- `name`: Display name

**Returns:** True if successful

##### start_stream()
```python
def start_stream(self, stream_id: str) -> bool
```
Start streaming.

##### stop_stream()
```python
def stop_stream(self, stream_id: str) -> None
```
Stop streaming.

##### get_image_provider()
```python
def get_image_provider(self, stream_id: str) -> ImageProvider
```
Get QML image provider for stream.

**Example:**
```python
video = VideoStreamHandler()

# Add camera stream
video.add_stream("front_cam", "rtsp://192.168.1.100:554/stream", "Front Camera")

# Start streaming
video.start_stream("front_cam")

# Use in QML (register image provider first)
# Image { source: "image://front_cam" }
```

---

### WorkFlowRunner

Executes YAML-based workflows.

**Module**: `paint_controller.services.workflow.workflow_runner`

#### Class: WorkFlowRunner(QObject)

**Constructor:**
```python
WorkFlowRunner(hardware_controllers: dict)
```

**Parameters:**
- `hardware_controllers`: Dict of hardware controller references

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_running` | bool | Workflow running state |
| `is_paused` | bool | Workflow paused state |
| `progress` | float | Progress (0.0 to 1.0) |
| `current_action` | str | Current action ID |

**Signals:**
- `workflow_started`: Workflow began execution
- `workflow_completed`: Workflow completed successfully
- `workflow_failed(str)`: Workflow failed (error message)
- `workflow_paused`: Workflow paused
- `workflow_resumed`: Workflow resumed
- `action_started(str)`: Action started (action ID)
- `action_completed(str)`: Action completed (action ID)
- `progress_changed`: Progress updated

**Methods:**

##### load_workflow()
```python
def load_workflow(self, workflow_path: str) -> bool
```
Load workflow from YAML file.

**Parameters:**
- `workflow_path`: Path to workflow YAML file

**Returns:** True if loaded successfully

##### start()
```python
@Slot()
def start(self) -> None
```
Start workflow execution.

##### stop()
```python
@Slot()
def stop(self) -> None
```
Stop workflow execution.

##### pause()
```python
@Slot()
def pause(self) -> None
```
Pause workflow execution.

##### resume()
```python
@Slot()
def resume(self) -> None
```
Resume paused workflow.

**Example:**
```python
# Create runner
runner = WorkFlowRunner({
    'winch': winch_controller,
    'wheel': wheel_controller
})

# Connect signals
runner.workflow_started.connect(lambda: print("Workflow started"))
runner.workflow_completed.connect(lambda: print("Workflow completed"))
runner.progress_changed.connect(lambda: print(f"Progress: {runner.progress * 100}%"))

# Load and run
if runner.load_workflow("workflows/ascend.yaml"):
    runner.start()
```

---

### ScreenRecorder

Records application screen.

**Module**: `paint_controller.services.screen_recorder`

#### Class: ScreenRecorder(QObject)

**Constructor:**
```python
ScreenRecorder()
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_recording` | bool | Recording state |
| `output_path` | str | Current output file path |

**Signals:**
- `recording_started`: Recording began
- `recording_stopped`: Recording stopped
- `recording_error(str)`: Error occurred

**Methods:**

##### start_recording()
```python
def start_recording(self, output_path: str) -> bool
```
Start screen recording.

**Parameters:**
- `output_path`: Where to save the recording

**Returns:** True if started successfully

##### stop_recording()
```python
def stop_recording(self) -> None
```
Stop recording and save file.

**Example:**
```python
recorder = ScreenRecorder()

# Start recording
recorder.start_recording("/tmp/screen_recording.mp4")

# ... do things ...

# Stop and save
recorder.stop_recording()
```

---

## Models

### ActionConfigPython

Configuration for workflow actions.

**Module**: `paint_controller.models.action_config`

#### Class: ActionConfigPython

**Attributes:**
- `action_id` (str): Unique action identifier
- `action_type` (str): Type of action
- `parameters` (dict): Action parameters
- `start_time` (float): When to start (seconds)
- `wait_for_completion` (bool): Wait for completion

**Example:**
```python
config = ActionConfigPython(
    action_id="move_winch",
    action_type="winch_absolute",
    parameters={"length": 5000, "speed": 150},
    wait_for_completion=True
)
```

---

## Widgets

### VTKPointCloudWidget

Qt widget for 3D point cloud visualization.

**Module**: `paint_controller.widgets.vtk_pointcloud`

#### Class: VTKPointCloudWidget(QWidget)

**Constructor:**
```python
VTKPointCloudWidget(parent=None)
```

**Methods:**

##### set_point_cloud()
```python
def set_point_cloud(self, points: np.ndarray) -> None
```
Set point cloud data.

**Parameters:**
- `points`: Numpy array of shape (N, 3) with XYZ coordinates

##### clear()
```python
def clear(self) -> None
```
Clear point cloud display.

##### reset_camera()
```python
def reset_camera(self) -> None
```
Reset camera to default view.

**Example:**
```python
import numpy as np

widget = VTKPointCloudWidget()

# Create sample points
points = np.random.rand(1000, 3)

# Display
widget.set_point_cloud(points)

# Embed in layout
layout.addWidget(widget)
```

---

## QML Integration

### Accessing Controllers from QML

Controllers are exposed to QML via context properties:

```qml
import QtQuick 2.15

Item {
    // Access properties
    Text {
        text: "Winch position: " + winchController.position + " mm"
    }
    
    // Call methods
    Button {
        text: "Emergency Stop"
        onClicked: robotController.emergency_stop()
    }
    
    // React to signals
    Connections {
        target: winchController
        function onPositionChanged() {
            console.log("Position updated:", winchController.position)
        }
    }
}
```

### Available Context Properties

| Property Name | Python Object |
|---------------|---------------|
| `robotController` | RobotController |
| `winchController` | WinchController |
| `wheelController` | WheelController |
| `lidarController` | LidarController |
| `teensyController` | TeensyController |
| `systemMonitor` | SystemMonitor |
| `steamDeck` | SteamDeckHandler |
| `videoHandler` | VideoStreamHandler |
| `workflowRunner` | WorkFlowRunner |
| `settings` | SettingsManager |

---

## Usage Patterns

### Pattern 1: Creating a New Controller

```python
from PySide6.QtCore import QObject, Signal, Property
from rclpy.node import Node

class MyController(QObject):
    # Define signals
    value_changed = Signal()
    
    def __init__(self, robot_controller: Node):
        super().__init__()
        self._robot_controller = robot_controller
        self._value = 0.0
        self._setup_ros()
    
    def _setup_ros(self):
        # Create subscribers/publishers
        self._sub = self._robot_controller.create_subscription(
            MyMsg, '/my/topic', self._callback, 10
        )
    
    def _callback(self, msg):
        self.value = msg.value
    
    # Qt Property for QML
    @Property(float, notify=value_changed)
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        if self._value != v:
            self._value = v
            self.value_changed.emit()
```

### Pattern 2: Publishing from Controller

```python
class MyController(QObject):
    def __init__(self, robot_controller: Node):
        super().__init__()
        self._pub = robot_controller.create_publisher(
            Twist, '/cmd_vel', 10
        )
    
    @Slot(float)
    def send_command(self, value: float):
        msg = Twist()
        msg.linear.x = value
        self._pub.publish(msg)
```

### Pattern 3: Cross-Thread Communication

```python
class MyController(QObject):
    # Define signal in main thread
    data_ready = Signal(float)
    
    def __init__(self, robot_controller):
        super().__init__()
        self._sub = robot_controller.create_subscription(
            Float32, '/topic', self._callback, 10
        )
    
    def _callback(self, msg):
        # This runs in ROS thread
        # Emit signal (automatically queued to main thread)
        self.data_ready.emit(msg.data)
```

---

## Type Hints

The API uses type hints throughout. Common types:

```python
from typing import Optional, List, Dict, Tuple, Callable, Any
from PySide6.QtCore import QObject, Signal, Property, Slot
from rclpy.node import Node
import numpy as np
```

---

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [WORKFLOWS.md](WORKFLOWS.md) - Workflow system guide
- [README.md](README.md) - General usage and installation

---

**Note**: This API reference documents the Python version only. The C++ version is no longer maintained.
