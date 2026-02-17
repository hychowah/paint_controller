"""
Unit tests for WheelViewModel

Tests ViewModel pattern implementation, property bindings, and service integration.
"""

import pytest
from unittest.mock import Mock
from PySide6.QtCore import QObject, Signal


# Mock WheelController for testing
class MockWheelController(QObject):
    """Mock WheelController for testing"""
    
    # Define signals
    left_wheel_speed_changed = Signal()
    right_wheel_speed_changed = Signal()
    left_wheel_current_changed = Signal()
    right_wheel_current_changed = Signal()
    left_wheel_position_changed = Signal()
    right_wheel_position_changed = Signal()
    available_changed = Signal()
    enabled_changed = Signal()
    left_error_changed = Signal()
    right_error_changed = Signal()
    left_motor_available_changed = Signal()
    right_motor_available_changed = Signal()
    error_state_changed = Signal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.left_wheel_speed = 100.0
        self.right_wheel_speed = 100.0
        self.left_wheel_current = 5.0
        self.right_wheel_current = 5.0
        self.left_wheel_position = 1000.0
        self.right_wheel_position = 1000.0
        self.available = True
        self.enabled = True
        self.left_error = False
        self.right_error = False
        self.left_motor_available = True
        self.right_motor_available = True
        
        # Mock methods
        self.command_speed = Mock()
        self.command_position = Mock()
        self.emergency_stop = Mock()
        self.disable = Mock()
        self.set_zero = Mock()


class TestWheelViewModel:
    """Test cases for WheelViewModel"""
    
    @pytest.fixture
    def wheel_controller(self):
        """Fixture for mock wheel controller"""
        return MockWheelController()
    
    @pytest.fixture
    def view_model(self, wheel_controller):
        """Fixture for WheelViewModel"""
        from paint_controller.viewmodels.wheel_view_model import WheelViewModel
        return WheelViewModel(wheel_controller)
    
    def test_initialization(self, view_model, wheel_controller):
        """Test ViewModel initializes correctly"""
        assert view_model is not None
        assert view_model._controller is wheel_controller
    
    def test_left_wheel_speed_property(self, view_model, wheel_controller):
        """Test left_wheel_speed property returns controller value"""
        assert view_model.left_wheel_speed == 100.0
        
        wheel_controller.left_wheel_speed = 150.0
        assert view_model.left_wheel_speed == 150.0
    
    def test_right_wheel_speed_property(self, view_model, wheel_controller):
        """Test right_wheel_speed property returns controller value"""
        assert view_model.right_wheel_speed == 100.0
        
        wheel_controller.right_wheel_speed = 120.0
        assert view_model.right_wheel_speed == 120.0
    
    def test_left_wheel_current_property(self, view_model, wheel_controller):
        """Test left_wheel_current property returns controller value"""
        assert view_model.left_wheel_current == 5.0
    
    def test_right_wheel_current_property(self, view_model, wheel_controller):
        """Test right_wheel_current property returns controller value"""
        assert view_model.right_wheel_current == 5.0
    
    def test_left_wheel_position_property(self, view_model, wheel_controller):
        """Test left_wheel_position property returns controller value"""
        assert view_model.left_wheel_position == 1000.0
    
    def test_right_wheel_position_property(self, view_model, wheel_controller):
        """Test right_wheel_position property returns controller value"""
        assert view_model.right_wheel_position == 1000.0
    
    def test_available_property(self, view_model, wheel_controller):
        """Test available property returns controller value"""
        assert view_model.available is True
    
    def test_enabled_property(self, view_model, wheel_controller):
        """Test enabled property returns controller value"""
        assert view_model.enabled is True
    
    def test_left_error_property(self, view_model, wheel_controller):
        """Test left_error property returns controller value"""
        assert view_model.left_error is False
    
    def test_right_error_property(self, view_model, wheel_controller):
        """Test right_error property returns controller value"""
        assert view_model.right_error is False
    
    def test_left_motor_available_property(self, view_model, wheel_controller):
        """Test left_motor_available property returns controller value"""
        assert view_model.left_motor_available is True
    
    def test_right_motor_available_property(self, view_model, wheel_controller):
        """Test right_motor_available property returns controller value"""
        assert view_model.right_motor_available is True
    
    def test_command_speed(self, view_model, wheel_controller):
        """Test command_speed slot calls controller method"""
        view_model.command_speed(100.0, 100.0)
        wheel_controller.command_speed.assert_called_once_with(100.0, 100.0)
    
    def test_command_position(self, view_model, wheel_controller):
        """Test command_position slot calls controller method"""
        view_model.command_position(1500.0, 1500.0, 50.0)
        wheel_controller.command_position.assert_called_once_with(1500.0, 1500.0, 50.0)
    
    def test_stop(self, view_model, wheel_controller):
        """Test stop slot calls command_speed with 0"""
        view_model.stop()
        wheel_controller.command_speed.assert_called_once_with(0, 0)
    
    def test_emergency_stop(self, view_model, wheel_controller):
        """Test emergency_stop slot calls controller method"""
        view_model.emergency_stop()
        wheel_controller.emergency_stop.assert_called_once()
    
    def test_disable(self, view_model, wheel_controller):
        """Test disable slot calls controller method"""
        view_model.disable()
        wheel_controller.disable.assert_called_once()
    
    def test_set_zero(self, view_model, wheel_controller):
        """Test set_zero slot calls controller method"""
        view_model.set_zero()
        wheel_controller.set_zero.assert_called_once()
    
    def test_signal_forwarding(self, view_model, wheel_controller):
        """Test that ViewModel forwards controller signals"""
        signal_emitted = [False]
        
        def on_signal():
            signal_emitted[0] = True
        
        view_model.left_wheel_speed_changed.connect(on_signal)
        
        # Emit signal from controller
        wheel_controller.left_wheel_speed_changed.emit()
        
        # ViewModel should forward it
        assert signal_emitted[0]
    
    def test_multiple_signal_forwarding(self, view_model, wheel_controller):
        """Test that multiple signals are forwarded correctly"""
        signals_emitted = {
            'left_speed': False,
            'right_speed': False,
            'available': False
        }
        
        view_model.left_wheel_speed_changed.connect(lambda: signals_emitted.update({'left_speed': True}))
        view_model.right_wheel_speed_changed.connect(lambda: signals_emitted.update({'right_speed': True}))
        view_model.available_changed.connect(lambda: signals_emitted.update({'available': True}))
        
        # Emit signals from controller
        wheel_controller.left_wheel_speed_changed.emit()
        wheel_controller.right_wheel_speed_changed.emit()
        wheel_controller.available_changed.emit()
        
        # All should be forwarded
        assert signals_emitted['left_speed']
        assert signals_emitted['right_speed']
        assert signals_emitted['available']
    
    def test_error_state_signal_forwarding(self, view_model, wheel_controller):
        """Test that error_state_changed signal is forwarded with parameters"""
        error_info = {'has_error': None, 'message': None}
        
        def on_error(has_error, message):
            error_info['has_error'] = has_error
            error_info['message'] = message
        
        view_model.error_state_changed.connect(on_error)
        
        # Emit error signal from controller
        wheel_controller.error_state_changed.emit(True, "Motor fault detected")
        
        # ViewModel should forward it with parameters
        assert error_info['has_error'] is True
        assert error_info['message'] == "Motor fault detected"
