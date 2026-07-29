#!/usr/bin/env python3
"""
Standalone test script for Monitor UI (PageMonitor.qml)

This script allows testing the industrial monitor UI without the main application.
It creates mock controllers with simulated data to verify the UI functionality.

Usage:
    python test_industrial_monitor.py

The monitor UI will appear in a 1280x720 window with live simulated data.
"""

import math
import os
import random
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal
    from PySide6.QtQuick import QQuickView
    from PySide6.QtWidgets import QApplication

    class MockTeensyController(QObject):
        """Mock Teensy controller with simulated data"""

        status_changed = Signal(dict)

        def __init__(self):
            super().__init__()
            self._status = {
                "available": True,
                "voltage": 24.0,
                "temperature": 45.0,
                "loop_time": 2.0,
                "relay_on": True,
                "enabled": True,
                "arm_extension_dist": 1200.0,  # mm
                "arm_rail_current": 2.5,
                "spray_gun_motor_current": 1.8,
                "imu_pitch": 5.2,
                "imu_roll": -2.1,
                "imu_yaw": 87.5,
                "imu_acc_x": 0.02,
                "imu_acc_y": -0.01,
                "imu_acc_z": 1.01,
                "imu_angular_acc_x": 0.1,
                "imu_angular_acc_y": -0.05,
                "imu_angular_acc_z": 0.03,
                "valve_position": 65.0,
                "valve_rate": 12.5,
                "valve_motor_current": 0.8,
                "total_volumne": 45.3,
            }

            # Timer to simulate data updates
            self._timer = QTimer()
            self._timer.timeout.connect(self._update_data)
            self._timer.start(100)  # Update every 100ms

            self._time = 0

        def _update_data(self):
            """Simulate changing data"""
            self._time += 0.1

            # Simulate voltage fluctuation
            self._status["voltage"] = 24.0 + math.sin(self._time * 0.5) * 0.5

            # Simulate temperature rise
            self._status["temperature"] = 45.0 + math.sin(self._time * 0.2) * 3.0

            # Simulate loop time jitter
            self._status["loop_time"] = 2.0 + random.uniform(-0.3, 0.3)

            # Simulate arm movement
            self._status["arm_extension_dist"] = 1000.0 + 500.0 * (math.sin(self._time * 0.3) + 1) / 2
            self._status["arm_rail_current"] = 1.0 + 2.0 * abs(math.sin(self._time * 0.3))

            # Simulate IMU data
            self._status["imu_pitch"] = 5.0 + math.sin(self._time * 0.4) * 2.0
            self._status["imu_roll"] = -2.0 + math.cos(self._time * 0.5) * 1.5
            self._status["imu_acc_z"] = 1.0 + math.sin(self._time * 0.8) * 0.05

            # Simulate valve changes
            self._status["valve_rate"] = 10.0 + math.sin(self._time * 0.3) * 5.0
            self._status["total_volumne"] += 0.05

            # Emit signal
            self.status_changed.emit(self._status)

        @Property("QVariantMap", notify=status_changed)
        def all_status(self):
            return self._status

        def setEnabled(self, enabled):
            """Mock enable function"""
            self._status["enabled"] = enabled
            print(f"Teensy enabled: {enabled}")

    class MockWheelController(QObject):
        """Mock Wheel controller with simulated data"""

        left_wheel_speed_changed = Signal()
        right_wheel_speed_changed = Signal()
        left_wheel_current_changed = Signal()
        right_wheel_current_changed = Signal()
        left_motor_available_changed = Signal()
        right_motor_available_changed = Signal()

        def __init__(self):
            super().__init__()
            self._left_speed = 0.0
            self._right_speed = 0.0
            self._left_current = 0.0
            self._right_current = 0.0
            self._left_available = True
            self._right_available = True

            # Timer to simulate data updates
            self._timer = QTimer()
            self._timer.timeout.connect(self._update_data)
            self._timer.start(100)

            self._time = 0

        def _update_data(self):
            """Simulate changing wheel data"""
            self._time += 0.1

            # Simulate wheel speeds
            self._left_speed = 1.5 + math.sin(self._time * 0.4) * 0.5
            self._right_speed = 1.5 + math.sin(self._time * 0.4 + 0.1) * 0.5

            # Simulate currents
            self._left_current = abs(self._left_speed) * 1.5 + 0.5
            self._right_current = abs(self._right_speed) * 1.5 + 0.5

            # Emit signals
            self.left_wheel_speed_changed.emit()
            self.right_wheel_speed_changed.emit()
            self.left_wheel_current_changed.emit()
            self.right_wheel_current_changed.emit()

        @Property(float, notify=left_wheel_speed_changed)
        def left_wheel_speed(self):
            return self._left_speed

        @Property(float, notify=right_wheel_speed_changed)
        def right_wheel_speed(self):
            return self._right_speed

        @Property(float, notify=left_wheel_current_changed)
        def left_wheel_current(self):
            return self._left_current

        @Property(float, notify=right_wheel_current_changed)
        def right_wheel_current(self):
            return self._right_current

        @Property(bool, notify=left_motor_available_changed)
        def left_motor_available(self):
            return self._left_available

        @Property(bool, notify=right_motor_available_changed)
        def right_motor_available(self):
            return self._right_available

        def setEnabled(self, enabled):
            """Mock enable function"""
            print(f"Wheel enabled: {enabled}")

    class MockWinchController(QObject):
        """Mock Winch controller with simulated data"""

        cable_length_changed = Signal()
        cable_speed_changed = Signal()
        motor_voltage_changed = Signal()
        motor_temperature_changed = Signal()
        winch_torque_changed = Signal()

        def __init__(self):
            super().__init__()
            self._cable_length = 25000.0  # mm
            self._cable_speed = 0.0
            self._motor_voltage = 24.0
            self._motor_temperature = 38.0
            self._winch_torque = 45.0

            # Timer to simulate data updates
            self._timer = QTimer()
            self._timer.timeout.connect(self._update_data)
            self._timer.start(100)

            self._time = 0
            self._direction = 1

        def _update_data(self):
            """Simulate changing winch data"""
            self._time += 0.1

            # Simulate cable movement
            self._cable_speed = math.sin(self._time * 0.3) * 0.3
            self._cable_length += self._cable_speed * 100

            # Keep cable length in bounds
            if self._cable_length < 10000:
                self._cable_length = 10000
                self._direction = 1
            elif self._cable_length > 50000:
                self._cable_length = 50000
                self._direction = -1

            # Simulate torque based on speed
            self._winch_torque = 30.0 + abs(self._cable_speed) * 50.0 + random.uniform(-5, 5)

            # Simulate voltage and temperature
            self._motor_voltage = 24.0 + math.sin(self._time * 0.2) * 0.3
            self._motor_temperature = 38.0 + abs(self._cable_speed) * 20.0

            # Emit signals
            self.cable_length_changed.emit()
            self.cable_speed_changed.emit()
            self.motor_voltage_changed.emit()
            self.motor_temperature_changed.emit()
            self.winch_torque_changed.emit()

        @Property(float, notify=cable_length_changed)
        def cable_length(self):
            return self._cable_length

        @Property(float, notify=cable_speed_changed)
        def cable_speed(self):
            return self._cable_speed

        @Property(float, notify=motor_voltage_changed)
        def motor_voltage(self):
            return self._motor_voltage

        @Property(float, notify=motor_temperature_changed)
        def motor_temperature(self):
            return self._motor_temperature

        @Property(float, notify=winch_torque_changed)
        def winch_torque(self):
            return self._winch_torque

        def setEnabled(self, enabled):
            """Mock enable function"""
            print(f"Winch enabled: {enabled}")

    def test_monitor_ui():
        """Test the monitor UI with mock controllers"""
        print("=" * 60)
        print("Industrial Monitor UI Test")
        print("=" * 60)
        print("\nStarting standalone monitor test...")
        print("This will open a 1280x720 window with simulated data.")
        print("Press Ctrl+C to exit.\n")

        app = QApplication(sys.argv)
        app.setApplicationName("Paint Controller Monitor Test")

        # Create mock controllers
        print("Creating mock controllers...")
        teensy_controller = MockTeensyController()
        wheel_controller = MockWheelController()
        winch_controller = MockWinchController()

        # Path to the QML file
        qml_file = os.path.join(os.path.dirname(__file__), "..", "qml", "pages", "status", "PageMonitor.qml")

        abs_qml_file = os.path.abspath(qml_file)
        print(f"Loading QML from: {abs_qml_file}")

        if not os.path.exists(abs_qml_file):
            print(f"❌ ERROR: QML file not found: {abs_qml_file}")
            return False

        # Use QQuickView to display Rectangle-based QML
        view = QQuickView()
        view.setTitle("Industrial Monitor Test - 1280x720")
        view.setResizeMode(QQuickView.SizeRootObjectToView)
        view.setWidth(1280)
        view.setHeight(720)

        # Expose controllers to QML
        view.rootContext().setContextProperty("teensyController", teensy_controller)
        view.rootContext().setContextProperty("wheelController", wheel_controller)
        view.rootContext().setContextProperty("winchController", winch_controller)

        # Load the QML file
        view.setSource(QUrl.fromLocalFile(abs_qml_file))

        if view.status() == QQuickView.Error:
            print("❌ ERROR: Failed to load QML file")
            for error in view.errors():
                print(f"  - {error.toString()}")
            return False

        view.show()

        print("✅ QML file loaded successfully!")
        print("\n" + "=" * 60)
        print("Monitor UI is running with simulated data")
        print("=" * 60)
        print("\nSimulated data features:")
        print("  • Voltage fluctuating around 24V")
        print("  • Temperature varying around 45°C")
        print("  • Arm extending/retracting")
        print("  • Wheels moving with varying speeds")
        print("  • Winch cable moving up/down")
        print("  • IMU data simulating movement")
        print("  • Valve flow rate changing")
        print("\nPress the Emergency Stop button to test disable functionality")
        print("Press Ctrl+C to exit\n")

        # Run the application
        return app.exec()

    if __name__ == "__main__":
        try:
            exit_code = test_monitor_ui()
            sys.exit(exit_code)
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            sys.exit(0)

except ImportError as e:
    print("=" * 60)
    print("PySide6 Not Available")
    print("=" * 60)
    print(f"\n⚠️  Error: {e}")
    print("\nThis test requires PySide6 to be installed.")
    print("\nTo install PySide6:")
    print("  pip install PySide6")
    print("\nNote: This is expected in CI environments.")
    print("Run this test on actual hardware with PySide6 installed.")
    print("\n" + "=" * 60)
    sys.exit(0)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
