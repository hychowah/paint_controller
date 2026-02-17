"""
Unit tests for ESP32ValveViewModel

Tests ViewModel pattern implementation, property bindings, and service integration.
"""

import pytest
from unittest.mock import Mock
from PySide6.QtCore import QObject, Signal


# Mock ESP32ValveController for testing
class MockESP32ValveController(QObject):
    """Mock ESP32ValveController for testing"""
    
    # Define signals
    valve_position_changed = Signal(float)
    valve_motor_current_changed = Signal(int)
    flow_rate_changed = Signal(float)
    total_volume_changed = Signal(float)
    valve_motor_connected_changed = Signal(bool)
    flow_meter_connected_changed = Signal(bool)
    available_changed = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self._valve_position = 50.0
        self._valve_motor_current = 100
        self._valve_rate = 5.5
        self._total_volume = 1000.0
        self._valve_motor_connected = True
        self._flow_meter_connected = True
        self._available = True
        
        # Mock methods
        self.setValveTurn = Mock()


class TestESP32ValveViewModel:
    """Test cases for ESP32ValveViewModel"""
    
    @pytest.fixture
    def valve_controller(self):
        """Fixture for mock valve controller"""
        return MockESP32ValveController()
    
    @pytest.fixture
    def view_model(self, valve_controller):
        """Fixture for ESP32ValveViewModel"""
        from paint_controller.viewmodels.esp32_valve_view_model import ESP32ValveViewModel
        return ESP32ValveViewModel(valve_controller)
    
    def test_initialization(self, view_model, valve_controller):
        """Test ViewModel initializes correctly"""
        assert view_model is not None
        assert view_model._controller is valve_controller
    
    # Test properties
    
    def test_valve_position_property(self, view_model, valve_controller):
        """Test valve_position property returns controller value"""
        assert view_model.valve_position == 50.0
        
        valve_controller._valve_position = 75.0
        assert view_model.valve_position == 75.0
    
    def test_valve_motor_current_property(self, view_model, valve_controller):
        """Test valve_motor_current property returns controller value"""
        assert view_model.valve_motor_current == 100
        
        valve_controller._valve_motor_current = 150
        assert view_model.valve_motor_current == 150
    
    def test_flow_rate_property(self, view_model, valve_controller):
        """Test flow_rate property returns controller value"""
        assert view_model.flow_rate == 5.5
        
        valve_controller._valve_rate = 7.2
        assert view_model.flow_rate == 7.2
    
    def test_total_volume_property(self, view_model, valve_controller):
        """Test total_volume property returns controller value"""
        assert view_model.total_volume == 1000.0
        
        valve_controller._total_volume = 1500.0
        assert view_model.total_volume == 1500.0
    
    def test_valve_motor_connected_property(self, view_model, valve_controller):
        """Test valve_motor_connected property returns controller value"""
        assert view_model.valve_motor_connected is True
        
        valve_controller._valve_motor_connected = False
        assert view_model.valve_motor_connected is False
    
    def test_flow_meter_connected_property(self, view_model, valve_controller):
        """Test flow_meter_connected property returns controller value"""
        assert view_model.flow_meter_connected is True
        
        valve_controller._flow_meter_connected = False
        assert view_model.flow_meter_connected is False
    
    def test_available_property(self, view_model, valve_controller):
        """Test available property returns controller value"""
        assert view_model.available is True
        
        valve_controller._available = False
        assert view_model.available is False
    
    # Test slots
    
    def test_setValveTurn(self, view_model, valve_controller):
        """Test setValveTurn slot calls controller method"""
        view_model.setValveTurn(75.0)
        valve_controller.setValveTurn.assert_called_once_with(75.0)
    
    def test_closeValve(self, view_model, valve_controller):
        """Test closeValve slot calls setValveTurn with 0"""
        view_model.closeValve()
        valve_controller.setValveTurn.assert_called_once_with(0.0)
    
    def test_openValve(self, view_model, valve_controller):
        """Test openValve slot calls setValveTurn with 100"""
        view_model.openValve()
        valve_controller.setValveTurn.assert_called_once_with(100.0)
    
    # Test signal forwarding
    
    def test_valve_position_signal_forwarding(self, view_model, valve_controller):
        """Test that valve_position_changed signal is forwarded"""
        signal_emitted = [False]
        received_value = [None]
        
        def on_signal(value):
            signal_emitted[0] = True
            received_value[0] = value
        
        view_model.valve_position_changed.connect(on_signal)
        valve_controller.valve_position_changed.emit(80.0)
        
        assert signal_emitted[0]
        assert received_value[0] == 80.0
    
    def test_valve_motor_current_signal_forwarding(self, view_model, valve_controller):
        """Test that valve_motor_current_changed signal is forwarded"""
        signal_emitted = [False]
        received_value = [None]
        
        def on_signal(value):
            signal_emitted[0] = True
            received_value[0] = value
        
        view_model.valve_motor_current_changed.connect(on_signal)
        valve_controller.valve_motor_current_changed.emit(200)
        
        assert signal_emitted[0]
        assert received_value[0] == 200
    
    def test_available_signal_forwarding(self, view_model, valve_controller):
        """Test that available_changed signal is forwarded"""
        signal_emitted = [False]
        
        def on_signal(available):
            signal_emitted[0] = True
        
        view_model.available_changed.connect(on_signal)
        valve_controller.available_changed.emit(False)
        
        assert signal_emitted[0]
    
    def test_multiple_signal_forwarding(self, view_model, valve_controller):
        """Test that multiple signals are forwarded correctly"""
        signals_emitted = {
            'position': False,
            'flow_rate': False,
            'total_volume': False,
            'motor_connected': False,
            'flow_connected': False
        }
        
        view_model.valve_position_changed.connect(
            lambda x: signals_emitted.update({'position': True}))
        view_model.flow_rate_changed.connect(
            lambda x: signals_emitted.update({'flow_rate': True}))
        view_model.total_volume_changed.connect(
            lambda x: signals_emitted.update({'total_volume': True}))
        view_model.valve_motor_connected_changed.connect(
            lambda x: signals_emitted.update({'motor_connected': True}))
        view_model.flow_meter_connected_changed.connect(
            lambda x: signals_emitted.update({'flow_connected': True}))
        
        # Emit signals from controller
        valve_controller.valve_position_changed.emit(90.0)
        valve_controller.flow_rate_changed.emit(8.5)
        valve_controller.total_volume_changed.emit(2000.0)
        valve_controller.valve_motor_connected_changed.emit(True)
        valve_controller.flow_meter_connected_changed.emit(True)
        
        # All should be forwarded
        assert signals_emitted['position']
        assert signals_emitted['flow_rate']
        assert signals_emitted['total_volume']
        assert signals_emitted['motor_connected']
        assert signals_emitted['flow_connected']
    
    def test_valve_control_workflow(self, view_model, valve_controller):
        """Test complete valve control workflow"""
        # Start with valve closed
        view_model.closeValve()
        assert valve_controller.setValveTurn.call_count == 1
        assert valve_controller.setValveTurn.call_args[0][0] == 0.0
        
        # Open to 50%
        view_model.setValveTurn(50.0)
        assert valve_controller.setValveTurn.call_count == 2
        assert valve_controller.setValveTurn.call_args[0][0] == 50.0
        
        # Fully open
        view_model.openValve()
        assert valve_controller.setValveTurn.call_count == 3
        assert valve_controller.setValveTurn.call_args[0][0] == 100.0
