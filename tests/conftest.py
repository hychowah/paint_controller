"""
Pytest configuration and shared fixtures.

Provides common fixtures and setup for all tests.
"""

import pytest
import sys
import os
import importlib.util
from pathlib import Path

# Add the paint_controller module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))


def load_module_from_file(module_name, file_path):
    """Load a Python module directly from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def service_container():
    """Fixture for ServiceContainer"""
    # Load service_container module directly to avoid ROS dependencies
    base_path = Path(__file__).parent.parent / 'python' / 'paint_controller' / 'core'
    module = load_module_from_file('service_container', base_path / 'service_container.py')
    
    container = module.ServiceContainer()
    yield container
    container.cleanup_all()


@pytest.fixture
def mock_winch_controller():
    """Fixture for a mock WinchController"""
    from unittest.mock import Mock
    from PySide6.QtCore import Signal
    
    mock = Mock()
    
    # Add signals
    mock.cable_length_changed = Signal(float)
    mock.cable_speed_changed = Signal(float)
    mock.winch_torque_changed = Signal(float)
    mock.motor_temperature_changed = Signal(float)
    mock.motor_voltage_changed = Signal(float)
    mock.motor_brake_changed = Signal(bool)
    mock.available_changed = Signal(bool)
    mock.enabled_changed = Signal(bool)
    
    # Add properties
    mock.cable_length = 1000.0
    mock.cable_speed = 50.0
    mock.winch_torque = 10.0
    mock.motor_temperature = 25.0
    mock.motor_voltage = 24.0
    mock.motor_brake = True
    mock.available = True
    mock.enabled = False
    mock.max_speed = 400.0
    
    return mock


@pytest.fixture
def mock_ros_node():
    """Fixture for a mock ROS node"""
    from unittest.mock import Mock
    
    mock = Mock()
    mock.create_publisher = Mock(return_value=Mock())
    mock.create_subscription = Mock(return_value=Mock())
    mock.destroy_node = Mock()
    
    return mock
