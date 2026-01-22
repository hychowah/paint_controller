# Running Paint Controller UI Without ROS

The paint_controller UI can now run in **standalone mode** without ROS2 installed. This is useful for:
- UI development and testing
- Debugging without a full ROS environment
- Faster iteration cycles

## How It Works

The application automatically detects if ROS2 is available:
- **With ROS2**: Full functionality with hardware integration
- **Without ROS2**: UI-only mode with mock ROS interfaces

When ROS2 is not available, the application uses lightweight mock implementations that:
- Accept all ROS calls without errors
- Log debug information
- Allow the UI to function normally
- Don't communicate with actual hardware

## Running in Standalone Mode

### Prerequisites

Install only the UI dependencies (no ROS required):

```bash
pip install PySide6 numpy PyYAML hidapi
```

### Run the Application

```bash
python3 -m paint_controller
# or
paint_controller
```

You should see:
```
⚠️  ROS2 not available - running in standalone UI mode
✓ Running in standalone UI mode (no ROS)
```

## What Works in Standalone Mode

✅ **Full UI functionality**
- All QML interfaces load correctly
- Navigation and controls work
- Settings management
- Video stream UI (streams won't actually connect)

✅ **Mock hardware controllers**
- All controller objects are created
- Method calls succeed (but don't control hardware)
- Properties can be read/written
- Signals are emitted

✅ **Development workflow**
- Modify QML files and see changes
- Test UI layouts and interactions
- Debug Qt/QML issues
- Validate control logic

## What Doesn't Work

❌ **Hardware communication**
- No actual ROS topics/services
- No hardware control (wheels, winch, etc.)
- No sensor data (lidar, IMU, etc.)
- Video streams won't connect to cameras

❌ **ROS-dependent features**
- Bag recording
- ROS-based workflow actions
- Cross-device communication

## Implementation Details

### Mock System

The mock system is in `paint_controller/core/ros_mock.py` and provides:

- `MockNode` - Lightweight node that logs calls
- `MockPublisher` - No-op publisher
- `MockSubscription` - Subscription that never receives data
- Mock message types (UInt8, Float32, Bool, etc.)

### Automatic Detection

All ROS-dependent modules use try/except to detect availability:

```python
try:
    import rclpy
    from std_msgs.msg import Float32
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    from paint_controller.core.ros_mock import MockFloat32 as Float32
```

### Modified Files

The following files have been updated for optional ROS:

- `core/application.py` - Main application with ROS detection
- `core/ros_mock.py` - Mock ROS interfaces (new file)
- `controllers/teensy.py` - Optional ROS imports
- `controllers/wheel.py` - Optional ROS imports
- `controllers/winch.py` - Optional ROS imports
- `controllers/wind_monitor.py` - Optional ROS imports
- `controllers/lidar.py` - Optional ROS imports
- `handlers/heartbeat.py` - Optional ROS imports
- `handlers/control_processor.py` - Optional ROS imports
- `services/workflow_legacy.py` - Optional ROS imports
- `services/video_stream.py` - Already had optional ROS (pattern followed)

## Testing

To verify the standalone mode works:

```bash
# Run the ros_mock tests
python3 python/paint_controller/core/ros_mock.py

# Should output:
# ✅ All mock functionality works correctly!
```

## Tips for Development

1. **Use standalone mode for UI work** - Much faster than spinning up full ROS environment
2. **Test with ROS before deploying** - Verify hardware integration still works
3. **Mock data for testing** - Add timer-based mock data updates in standalone mode if needed
4. **Check ROS2_AVAILABLE flag** - Use it to conditionally enable/disable features

## Troubleshooting

### "ModuleNotFoundError: No module named 'PySide6'"

Install the UI dependencies:
```bash
pip install PySide6
```

### UI doesn't start

Check the terminal output for error messages. Common issues:
- Missing QML files - check paths
- X11/display issues - set QT_QPA_PLATFORM environment variable

### Want to force ROS mode

Unset any environment variables and ensure rclpy is installed:
```bash
pip install rclpy
```
