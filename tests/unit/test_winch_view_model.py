"""
Unit tests for WinchViewModel

Tests ViewModel pattern implementation, property bindings, and service integration.
"""

import pytest
from unittest.mock import Mock, MagicMock
from PySide6.QtCore import QObject, Signal


# We need to mock the WinchController before importing WinchViewModel
class MockWinchController(QObject):
    """Mock WinchController for testing"""
    
    # Define signals
    cable_length_changed = Signal()
    cable_speed_changed = Signal()
    winch_torque_changed = Signal()
    motor_temperature_changed = Signal()
    motor_voltage_changed = Signal()
    motor_brake_changed = Signal()
    available_changed = Signal()
    enabled_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.cable_length = 1000.0
        self.cable_speed = 50.0
        self.winch_torque = 10.0
        self.motor_temperature = 25.0
        self.motor_voltage = 24.0
        self.motor_brake = True
        self.available = True
        self.enabled = False
        self.max_speed = 400.0
        
        # Mock methods
        self.command_speed_rpm = Mock()
        self.command_speed_mmps = Mock()
        self.command_enable = Mock()
        self.move_increment = Mock()
        self.move_absolute = Mock()
        self.command_load_detection = Mock()


class TestWinchViewModel:
    """Test cases for WinchViewModel"""
    
    @pytest.fixture
    def winch_controller(self):
        """Fixture for mock winch controller"""
        return MockWinchController()
    
    @pytest.fixture
    def view_model(self, winch_controller):
        """Fixture for WinchViewModel"""
        from paint_controller.viewmodels.winch_view_model import WinchViewModel
        return WinchViewModel(winch_controller)
    
    def test_initialization(self, view_model, winch_controller):
        """Test ViewModel initializes correctly"""
        assert view_model is not None
        assert view_model._controller is winch_controller
    
    def test_cable_length_property(self, view_model, winch_controller):
        """Test cable_length property returns controller value"""
        assert view_model.cable_length == 1000.0
        
        winch_controller.cable_length = 1500.0
        assert view_model.cable_length == 1500.0
    
    def test_cable_speed_property(self, view_model, winch_controller):
        """Test cable_speed property returns controller value"""
        assert view_model.cable_speed == 50.0
        
        winch_controller.cable_speed = 75.0
        assert view_model.cable_speed == 75.0
    
    def test_winch_torque_property(self, view_model, winch_controller):
        """Test winch_torque property returns controller value"""
        assert view_model.winch_torque == 10.0
    
    def test_motor_temperature_property(self, view_model, winch_controller):
        """Test motor_temperature property returns controller value"""
        assert view_model.motor_temperature == 25.0
    
    def test_motor_voltage_property(self, view_model, winch_controller):
        """Test motor_voltage property returns controller value"""
        assert view_model.motor_voltage == 24.0
    
    def test_motor_brake_property(self, view_model, winch_controller):
        """Test motor_brake property returns controller value"""
        assert view_model.motor_brake is True
    
    def test_available_property(self, view_model, winch_controller):
        """Test available property returns controller value"""
        assert view_model.available is True
    
    def test_enabled_property(self, view_model, winch_controller):
        """Test enabled property returns controller value"""
        assert view_model.enabled is False
    
    def test_max_speed_property(self, view_model, winch_controller):
        """Test max_speed property returns controller value"""
        assert view_model.max_speed == 400.0
    
    def test_set_speed_rpm(self, view_model, winch_controller):
        """Test set_speed_rpm slot calls controller method"""
        view_model.set_speed_rpm(100.0)
        winch_controller.command_speed_rpm.assert_called_once_with(100.0)
    
    def test_set_speed_mmps(self, view_model, winch_controller):
        """Test set_speed_mmps slot calls controller method"""
        view_model.set_speed_mmps(200.0)
        winch_controller.command_speed_mmps.assert_called_once_with(200.0)
    
    def test_set_enabled(self, view_model, winch_controller):
        """Test set_enabled slot calls controller method"""
        view_model.set_enabled(True)
        winch_controller.command_enable.assert_called_once_with(True)
    
    def test_move_increment(self, view_model, winch_controller):
        """Test move_increment slot calls controller method"""
        view_model.move_increment(100.0, 50.0)
        winch_controller.move_increment.assert_called_once_with(100.0, 50.0)
    
    def test_move_absolute(self, view_model, winch_controller):
        """Test move_absolute slot calls controller method"""
        view_model.move_absolute(1500.0, 75.0)
        winch_controller.move_absolute.assert_called_once_with(1500.0, 75.0)
    
    def test_stop(self, view_model, winch_controller):
        """Test stop slot calls command_speed_rpm with 0"""
        view_model.stop()
        winch_controller.command_speed_rpm.assert_called_once_with(0)
    
    def test_set_load_detection(self, view_model, winch_controller):
        """Test set_load_detection slot calls controller method"""
        view_model.set_load_detection(True)
        winch_controller.command_load_detection.assert_called_once_with(True)
    
    def test_signal_forwarding(self, view_model, winch_controller):
        """Test that ViewModel forwards controller signals"""
        # Create a spy to track signal emissions
        signal_emitted = [False]
        
        def on_signal():
            signal_emitted[0] = True
        
        view_model.cable_length_changed.connect(on_signal)
        
        # Emit signal from controller
        winch_controller.cable_length_changed.emit()
        
        # ViewModel should forward it
        assert signal_emitted[0]
    
    def test_multiple_signal_forwarding(self, view_model, winch_controller):
        """Test that multiple signals are forwarded correctly"""
        signals_emitted = {
            'cable_length': False,
            'cable_speed': False,
            'enabled': False
        }
        
        view_model.cable_length_changed.connect(lambda: signals_emitted.update({'cable_length': True}))
        view_model.cable_speed_changed.connect(lambda: signals_emitted.update({'cable_speed': True}))
        view_model.enabled_changed.connect(lambda: signals_emitted.update({'enabled': True}))
        
        # Emit signals from controller
        winch_controller.cable_length_changed.emit()
        winch_controller.cable_speed_changed.emit()
        winch_controller.enabled_changed.emit()
        
        # All should be forwarded
        assert signals_emitted['cable_length']
        assert signals_emitted['cable_speed']
        assert signals_emitted['enabled']
