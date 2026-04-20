"""Fixtures shared across all tests.

Utils modules (crc.py, input.py) are pure Python with zero external
dependencies. We import them *directly* by pre-loading the utils subpackage
before paint_controller/__init__.py can trigger PySide6/ROS2 imports.
"""

import os
import sys
import importlib
from pathlib import Path
import types

import pytest

from tests.fakes import FakeNode

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # Force offscreen — xcb may be set in environment but requires a display

# Add python/ directory to sys.path
_python_dir = Path(__file__).resolve().parent.parent / "python"
if str(_python_dir) not in sys.path:
    sys.path.insert(0, str(_python_dir))

# Pre-register paint_controller packages as namespace-only modules so submodule
# imports do not trigger heavy package-level __init__.py side effects.
if "paint_controller" not in sys.modules:
    _pkg = types.ModuleType("paint_controller")
    _pkg.__path__ = [str(_python_dir / "paint_controller")]
    _pkg.__package__ = "paint_controller"
    sys.modules["paint_controller"] = _pkg

if "paint_controller.utils" not in sys.modules:
    _utils_pkg = types.ModuleType("paint_controller.utils")
    _utils_pkg.__path__ = [str(_python_dir / "paint_controller" / "utils")]
    _utils_pkg.__package__ = "paint_controller.utils"
    sys.modules["paint_controller.utils"] = _utils_pkg

if "paint_controller.handlers" not in sys.modules:
    _handlers_pkg = types.ModuleType("paint_controller.handlers")
    _handlers_pkg.__path__ = [str(_python_dir / "paint_controller" / "handlers")]
    _handlers_pkg.__package__ = "paint_controller.handlers"
    sys.modules["paint_controller.handlers"] = _handlers_pkg

if "paint_controller.controllers" not in sys.modules:
    _controllers_pkg = types.ModuleType("paint_controller.controllers")
    _controllers_pkg.__path__ = [str(_python_dir / "paint_controller" / "controllers")]
    _controllers_pkg.__package__ = "paint_controller.controllers"
    sys.modules["paint_controller.controllers"] = _controllers_pkg

if "paint_controller.core" not in sys.modules:
    _core_pkg = types.ModuleType("paint_controller.core")
    _core_pkg.__path__ = [str(_python_dir / "paint_controller" / "core")]
    _core_pkg.__package__ = "paint_controller.core"
    sys.modules["paint_controller.core"] = _core_pkg


def _install_test_module_stubs() -> None:
    try:
        importlib.import_module("rclpy.node")
    except ModuleNotFoundError:
        rclpy_pkg = sys.modules.setdefault("rclpy", types.ModuleType("rclpy"))
        node_mod = types.ModuleType("rclpy.node")

        class Node:
            pass

        node_mod.Node = Node
        rclpy_pkg.node = node_mod
        sys.modules["rclpy.node"] = node_mod

    try:
        importlib.import_module("std_msgs.msg")
    except ModuleNotFoundError:
        std_msgs_pkg = sys.modules.setdefault("std_msgs", types.ModuleType("std_msgs"))
        msg_mod = types.ModuleType("std_msgs.msg")

        class Float32:
            def __init__(self):
                self.data = 0.0

        class Float64:
            def __init__(self):
                self.data = 0.0

        class Float32MultiArray:
            def __init__(self):
                self.data = []

        class Int32:
            def __init__(self):
                self.data = 0

        class Int32MultiArray:
            def __init__(self):
                self.data = []

        class Bool:
            def __init__(self):
                self.data = False

        msg_mod.Float32 = Float32
        msg_mod.Float64 = Float64
        msg_mod.Float32MultiArray = Float32MultiArray
        msg_mod.Int32 = Int32
        msg_mod.Int32MultiArray = Int32MultiArray
        msg_mod.Bool = Bool
        std_msgs_pkg.msg = msg_mod
        sys.modules["std_msgs.msg"] = msg_mod

    try:
        importlib.import_module("geometry_msgs.msg")
    except ModuleNotFoundError:
        geometry_msgs_pkg = sys.modules.setdefault("geometry_msgs", types.ModuleType("geometry_msgs"))
        msg_mod = types.ModuleType("geometry_msgs.msg")

        class Vector3:
            def __init__(self, x=0.0, y=0.0, z=0.0):
                self.x = x
                self.y = y
                self.z = z

        class Twist:
            def __init__(self):
                self.linear = Vector3()
                self.angular = Vector3()

        msg_mod.Vector3 = Vector3
        msg_mod.Twist = Twist
        geometry_msgs_pkg.msg = msg_mod
        sys.modules["geometry_msgs.msg"] = msg_mod

    try:
        importlib.import_module("paint_interfaces.msg")
    except ModuleNotFoundError:
        paint_interfaces_pkg = sys.modules.setdefault("paint_interfaces", types.ModuleType("paint_interfaces"))
        msg_mod = types.ModuleType("paint_interfaces.msg")

        class WinchStatus:
            def __init__(
                self,
                enabled=False,
                cable_length=0.0,
                cable_speed=0.0,
                winch_torque=0.0,
                motor_temperature=0.0,
                motor_voltage=0.0,
                motor_brake=True,
                load_detection_mode=False,
                unusual_load_detected=False,
            ):
                self.enabled = enabled
                self.cable_length = cable_length
                self.cable_speed = cable_speed
                self.winch_torque = winch_torque
                self.motor_temperature = motor_temperature
                self.motor_voltage = motor_voltage
                self.motor_brake = motor_brake
                self.load_detection_mode = load_detection_mode
                self.unusual_load_detected = unusual_load_detected

        class MoveWinchLength:
            def __init__(self):
                self.length_mm = 0
                self.speed_mm_s = 0
                self.acceleration_rpm_s = 30

        class MoveVehicleSpd:
            def __init__(self):
                self.left_rpm = 0
                self.right_rpm = 0

        class MoveVehiclePos:
            def __init__(self):
                self.left_travel_mm = 0
                self.right_travel_mm = 0
                self.rpm_limit = 0
                self.relative = True

        class VehicleStatus:
            def __init__(
                self,
                left_available=False,
                right_available=False,
                left_error=False,
                right_error=False,
                left_speed=0.0,
                right_speed=0.0,
                left_current=0.0,
                right_current=0.0,
                left_travel_mm=0.0,
                right_travel_mm=0.0,
            ):
                self.left_available = left_available
                self.right_available = right_available
                self.left_error = left_error
                self.right_error = right_error
                self.left_speed = left_speed
                self.right_speed = right_speed
                self.left_current = left_current
                self.right_current = right_current
                self.left_travel_mm = left_travel_mm
                self.right_travel_mm = right_travel_mm

        class ValveStatus:
            def __init__(self):
                self.valve_motor_current = 0
                self.valve_position = 0.0
                self.valve_rate = 0.0
                self.total_volume = 0.0
                self.valve_motor_connected = False
                self.flow_meter_connected = False

        class _Vector3:
            def __init__(self, x=0.0, y=0.0, z=0.0):
                self.x = x
                self.y = y
                self.z = z

        class TeensyStatus:
            def __init__(self):
                self.runtime = 0
                self.top_rail_position = 0.0
                self.top_rail_speed = 0.0
                self.top_rail_current = 0.0
                self.arm_rail_position = 0.0
                self.arm_rail_speed = 0.0
                self.arm_rail_current = 0.0
                self.arm_extension_dist = 0.0
                self.arm_sensor_dist = 0.0
                self.voltage = 0.0
                self.temperature = 0.0
                self.current = 0.0
                self.looptime = 0.0
                self.looptime_counter = 0
                self.relay_on = False
                self.enabled = False
                self.left_prop_position = 0.0
                self.left_prop_pwm = 0
                self.right_prop_position = 0.0
                self.right_prop_pwm = 0
                self.linear_acceleration = _Vector3()
                self.angular_velocity = _Vector3()
                self.orientation = _Vector3()
                self.spray_gun_pitch = 0.0
                self.gimbal_pitch_motor_angle = 0.0
                self.gimbal_pitch_motor_current = 0.0
                self.gimbal_pitch_motor_temp = 0.0
                self.gimbal_roll_motor_angle = 0.0
                self.gimbal_roll_motor_current = 0.0
                self.gimbal_roll_motor_temp = 0.0
                self.spray_gun_trigger = False
                self.yaw_enabled = False
                self.yaw_command = 0.0
                self.yaw_pid_p = 0.0
                self.yaw_pid_i = 0.0
                self.yaw_pid_d = 0.0

        class TeensyYaw:
            def __init__(self):
                self.yaw_enabled = False
                self.yaw_command = 0.0
                self.yaw_pid_p = 0.0
                self.yaw_pid_i = 0.0
                self.yaw_pid_d = 0.0
                self.yaw_pwm = 0

        msg_mod.WinchStatus = WinchStatus
        msg_mod.MoveWinchLength = MoveWinchLength
        msg_mod.MoveVehicleSpd = MoveVehicleSpd
        msg_mod.MoveVehiclePos = MoveVehiclePos
        msg_mod.VehicleStatus = VehicleStatus
        msg_mod.ValveStatus = ValveStatus
        msg_mod.TeensyStatus = TeensyStatus
        msg_mod.TeensyYaw = TeensyYaw
        paint_interfaces_pkg.msg = msg_mod
        sys.modules["paint_interfaces.msg"] = msg_mod


_install_test_module_stubs()


@pytest.fixture(scope="session")
def qt_app():
    """Create a headless QApplication for the entire test session.

    QApplication is a superset of QCoreApplication — using it everywhere
    prevents the dual-app conflict that aborts the suite when test ordering
    puts a qt_core_app user before a qt_app user (Qt allows only one app
    instance per process).
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(scope="session")
def qt_core_app(qt_app):
    """Alias of qt_app — guarantees QApplication is always created first.

    Tests that only need QObject/signal machinery (no widgets) can request
    this fixture for semantic clarity without risking a second app instance.
    """
    return qt_app


@pytest.fixture(autouse=True)
def _flush_qt_events(request):
    """Flush pending Qt events after each test.

    Session-scoped QApplication persists across all tests.  Without this,
    queued signals or timer callbacks from one test can fire during the next,
    causing ordering-dependent failures.
    """
    yield
    # Only flush if a Qt application exists (skips pure-Python tests)
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.processEvents()
    except Exception:  # pragma: no cover
        pass


@pytest.fixture
def fake_node() -> FakeNode:
    return FakeNode()

