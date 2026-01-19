# Testing the Industrial Monitor UI

## Standalone Test Script

The `test_industrial_monitor.py` script allows you to test the monitor UI without running the full application.

### Prerequisites

```bash
pip install PySide6
```

### Running the Test

```bash
cd ~/ros2_ws/src/paint_controller_ros2/python/paint_controller
python scripts/test_industrial_monitor.py
```

### What It Does

The script creates a standalone 1280x720 window showing the industrial monitor with:

- **Mock Controllers**: Simulates teensyController, wheelController, and winchController
- **Live Data**: All values update in real-time with realistic simulated behavior
- **Full Functionality**: Tests all UI components including:
  - Header telemetry (voltage, temperature, loop time)
  - Status badges (relay, system enable)
  - Emergency stop button
  - Wheel speeds and motor availability
  - Valve flow rate and position
  - Arm extension and currents
  - Winch cable data and motor telemetry
  - IMU sensor grid with sparklines

### Simulated Data Behavior

- **Voltage**: Fluctuates around 24V (±0.5V)
- **Temperature**: Varies around 45°C (±3°C)
- **Arm**: Extends/retracts between 1000-1500mm
- **Wheels**: Speed varies 1.0-2.0 m/s, current follows speed
- **Winch**: Cable moves up/down between 10-50m
- **IMU**: Simulates pitch, roll, yaw, and accelerations
- **Valves**: Flow rate varies 5-15 L/min, volume accumulates

### Testing Emergency Stop

Click the red "EMERGENCY STOP" button in the UI to verify:
- Console output confirms disable commands
- Button interaction works correctly
- Visual feedback is appropriate

### Expected Output

```
============================================================
Industrial Monitor UI Test
============================================================

Starting standalone monitor test...
This will open a 1280x720 window with simulated data.
Press Ctrl+C to exit.

Creating mock controllers...
Loading QML from: /path/to/PageMonitor.qml
✅ QML file loaded successfully!

============================================================
Monitor UI is running with simulated data
============================================================

Simulated data features:
  • Voltage fluctuating around 24V
  • Temperature varying around 45°C
  • Arm extending/retracting
  • Wheels moving with varying speeds
  • Winch cable moving up/down
  • IMU data simulating movement
  • Valve flow rate changing

Press the Emergency Stop button to test disable functionality
Press Ctrl+C to exit
```

### Troubleshooting

**"PySide6 not available"**
```bash
pip install PySide6
```

**"QML file not found"**
- Make sure you're running from the correct directory
- Check that `PageMonitor.qml` exists in `qml/pages/status/`

**Window doesn't appear**
- Check console for QML errors
- Verify all component files exist in `qml/components/displays/`

### File Structure Required

The test script requires these QML files:
```
qml/
├── pages/status/
│   └── PageMonitor.qml
└── components/displays/
    ├── MonitorHeader.qml
    ├── WheelsCard.qml
    ├── ValvesCard.qml
    ├── TeensyArmCard.qml
    ├── WinchCard.qml
    ├── IMUCard.qml
    ├── IndustrialCard.qml
    ├── ProgressBarIndicator.qml
    └── Sparkline.qml
```

## CI/CD Note

The script gracefully handles environments without PySide6 (like CI), printing an informative message instead of failing.
