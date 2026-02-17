"""
Unit tests for TeensyViewModel

Tests ViewModel pattern implementation, property bindings, and service integration.
"""

import pytest
from unittest.mock import Mock
from PySide6.QtCore import QObject, Signal


# Mock TeensyController for testing
class MockTeensyController(QObject):
    """Mock TeensyController for testing"""
    
    # Define signals
    status_changed = Signal(dict)
    connection_changed = Signal(bool)
    spray_gun_leveling_changed = Signal(bool)
    spray_gun_led_changed = Signal(bool)
    auto_correction_enabled_changed = Signal(bool)
    stability_enabled_changed = Signal(bool)
    thrust_force_changed = Signal(float)
    thrust_force_enabled_changed = Signal(bool)
    roller_steering_enabled_changed = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self._available = True
        
        # Mock methods
        self.setEnabled = Mock()
        self.setRelayEnabled = Mock()
        self.setTopRailSpeed = Mock()
        self.homeTopRail = Mock()
        self.setArmRailSpeed = Mock()
        self.extendArm = Mock()
        self.homeArm = Mock()
        self.setLeftPropPWM = Mock()
        self.setRightPropPWM = Mock()
        self.setLeftPropAngle = Mock()
        self.setRightPropAngle = Mock()
        self.setSprayTrigger = Mock()
        self.setSprayGunLeveling = Mock()
        self.setSprayGunLED = Mock()
        self.setGimbalTarget = Mock()
        self.setGimbalPID = Mock()
        self.setAutoCorrection = Mock()
        self.setStabilityEnabled = Mock()
        self.setYawEnabled = Mock()
        self.resetYaw = Mock()
        self.setRollerSteeringEnabled = Mock()
        self.setThrustForce = Mock()
        self.setYawPID = Mock()
        self.setStabilityPID = Mock()
        self.setTargetYaw = Mock()
        self.setYawCommand = Mock()
        self.setTargetYawAngle = Mock()
        self.setThrustForceEnabled = Mock()
        self.setValveRelay = Mock()
        self.get_status_value = Mock(return_value="test_value")
        self.get_formatted_value = Mock(return_value="formatted")


class TestTeensyViewModel:
    """Test cases for TeensyViewModel"""
    
    @pytest.fixture
    def teensy_controller(self):
        """Fixture for mock teensy controller"""
        return MockTeensyController()
    
    @pytest.fixture
    def view_model(self, teensy_controller):
        """Fixture for TeensyViewModel"""
        from paint_controller.viewmodels.teensy_view_model import TeensyViewModel
        return TeensyViewModel(teensy_controller)
    
    def test_initialization(self, view_model, teensy_controller):
        """Test ViewModel initializes correctly"""
        assert view_model is not None
        assert view_model._controller is teensy_controller
    
    def test_available_property(self, view_model, teensy_controller):
        """Test available property returns controller value"""
        assert view_model.available is True
        
        teensy_controller._available = False
        assert view_model.available is False
    
    # Test Enable/Relay control slots
    
    def test_setEnabled(self, view_model, teensy_controller):
        """Test setEnabled slot calls controller method"""
        view_model.setEnabled(True)
        teensy_controller.setEnabled.assert_called_once_with(True)
    
    def test_setRelayEnabled(self, view_model, teensy_controller):
        """Test setRelayEnabled slot calls controller method"""
        view_model.setRelayEnabled(True)
        teensy_controller.setRelayEnabled.assert_called_once_with(True)
    
    # Test Rail control slots
    
    def test_setTopRailSpeed(self, view_model, teensy_controller):
        """Test setTopRailSpeed slot calls controller method"""
        view_model.setTopRailSpeed(50.0)
        teensy_controller.setTopRailSpeed.assert_called_once_with(50.0)
    
    def test_homeTopRail(self, view_model, teensy_controller):
        """Test homeTopRail slot calls controller method"""
        view_model.homeTopRail(True)
        teensy_controller.homeTopRail.assert_called_once_with(True)
    
    def test_setArmRailSpeed(self, view_model, teensy_controller):
        """Test setArmRailSpeed slot calls controller method"""
        view_model.setArmRailSpeed(30.0)
        teensy_controller.setArmRailSpeed.assert_called_once_with(30.0)
    
    def test_extendArm(self, view_model, teensy_controller):
        """Test extendArm slot calls controller method"""
        view_model.extendArm(1000)
        teensy_controller.extendArm.assert_called_once_with(1000)
    
    def test_homeArm(self, view_model, teensy_controller):
        """Test homeArm slot calls controller method"""
        view_model.homeArm(True)
        teensy_controller.homeArm.assert_called_once_with(True)
    
    # Test Propeller control slots
    
    def test_setLeftPropPWM(self, view_model, teensy_controller):
        """Test setLeftPropPWM slot calls controller method"""
        view_model.setLeftPropPWM(1500)
        teensy_controller.setLeftPropPWM.assert_called_once_with(1500)
    
    def test_setRightPropPWM(self, view_model, teensy_controller):
        """Test setRightPropPWM slot calls controller method"""
        view_model.setRightPropPWM(1600)
        teensy_controller.setRightPropPWM.assert_called_once_with(1600)
    
    def test_setLeftPropAngle(self, view_model, teensy_controller):
        """Test setLeftPropAngle slot calls controller method"""
        view_model.setLeftPropAngle(45.0)
        teensy_controller.setLeftPropAngle.assert_called_once_with(45.0)
    
    def test_setRightPropAngle(self, view_model, teensy_controller):
        """Test setRightPropAngle slot calls controller method"""
        view_model.setRightPropAngle(30.0)
        teensy_controller.setRightPropAngle.assert_called_once_with(30.0)
    
    # Test Spray gun control slots
    
    def test_setSprayTrigger(self, view_model, teensy_controller):
        """Test setSprayTrigger slot calls controller method"""
        view_model.setSprayTrigger(1500)
        teensy_controller.setSprayTrigger.assert_called_once_with(1500)
    
    def test_setSprayGunLeveling(self, view_model, teensy_controller):
        """Test setSprayGunLeveling slot calls controller method"""
        view_model.setSprayGunLeveling(True)
        teensy_controller.setSprayGunLeveling.assert_called_once_with(True)
    
    def test_setSprayGunLED(self, view_model, teensy_controller):
        """Test setSprayGunLED slot calls controller method"""
        view_model.setSprayGunLED(True)
        teensy_controller.setSprayGunLED.assert_called_once_with(True)
    
    def test_setGimbalTarget(self, view_model, teensy_controller):
        """Test setGimbalTarget slot calls controller method"""
        view_model.setGimbalTarget(10.0, 15.0)
        teensy_controller.setGimbalTarget.assert_called_once_with(10.0, 15.0)
    
    def test_setGimbalPID(self, view_model, teensy_controller):
        """Test setGimbalPID slot calls controller method"""
        view_model.setGimbalPID(1.0, 0.5, 0.1, 2.0, 0.2)
        teensy_controller.setGimbalPID.assert_called_once_with(1.0, 0.5, 0.1, 2.0, 0.2)
    
    # Test Stability control slots
    
    def test_setAutoCorrection(self, view_model, teensy_controller):
        """Test setAutoCorrection slot calls controller method"""
        view_model.setAutoCorrection(True)
        teensy_controller.setAutoCorrection.assert_called_once_with(True)
    
    def test_setStabilityEnabled(self, view_model, teensy_controller):
        """Test setStabilityEnabled slot calls controller method"""
        view_model.setStabilityEnabled(True)
        teensy_controller.setStabilityEnabled.assert_called_once_with(True)
    
    # Test Yaw control slots
    
    def test_setYawEnabled(self, view_model, teensy_controller):
        """Test setYawEnabled slot calls controller method"""
        view_model.setYawEnabled(True)
        teensy_controller.setYawEnabled.assert_called_once_with(True)
    
    def test_resetYaw(self, view_model, teensy_controller):
        """Test resetYaw slot calls controller method"""
        view_model.resetYaw(True)
        teensy_controller.resetYaw.assert_called_once_with(True)
    
    def test_setRollerSteeringEnabled(self, view_model, teensy_controller):
        """Test setRollerSteeringEnabled slot calls controller method"""
        view_model.setRollerSteeringEnabled(True)
        teensy_controller.setRollerSteeringEnabled.assert_called_once_with(True)
    
    # Test Thrust control slots
    
    def test_setThrustForce(self, view_model, teensy_controller):
        """Test setThrustForce slot calls controller method"""
        view_model.setThrustForce(5.0)
        teensy_controller.setThrustForce.assert_called_once_with(5.0)
    
    def test_setYawPID(self, view_model, teensy_controller):
        """Test setYawPID slot calls controller method"""
        view_model.setYawPID(1.0, 0.5, 0.1)
        teensy_controller.setYawPID.assert_called_once_with(1.0, 0.5, 0.1)
    
    def test_setStabilityPID(self, view_model, teensy_controller):
        """Test setStabilityPID slot calls controller method"""
        view_model.setStabilityPID(2.0, 1.0, 0.2)
        teensy_controller.setStabilityPID.assert_called_once_with(2.0, 1.0, 0.2)
    
    def test_setTargetYaw(self, view_model, teensy_controller):
        """Test setTargetYaw slot calls controller method"""
        view_model.setTargetYaw(90.0, 80.0)
        teensy_controller.setTargetYaw.assert_called_once_with(90.0, 80.0)
    
    def test_setYawCommand(self, view_model, teensy_controller):
        """Test setYawCommand slot calls controller method"""
        view_model.setYawCommand(75.0)
        teensy_controller.setYawCommand.assert_called_once_with(75.0)
    
    def test_setTargetYawAngle(self, view_model, teensy_controller):
        """Test setTargetYawAngle slot calls controller method"""
        view_model.setTargetYawAngle(45.0)
        teensy_controller.setTargetYawAngle.assert_called_once_with(45.0)
    
    def test_setThrustForceEnabled(self, view_model, teensy_controller):
        """Test setThrustForceEnabled slot calls controller method"""
        view_model.setThrustForceEnabled(True)
        teensy_controller.setThrustForceEnabled.assert_called_once_with(True)
    
    def test_setValveRelay(self, view_model, teensy_controller):
        """Test setValveRelay slot calls controller method"""
        view_model.setValveRelay(True)
        teensy_controller.setValveRelay.assert_called_once_with(True)
    
    # Test status access methods
    
    def test_get_status_value(self, view_model, teensy_controller):
        """Test get_status_value calls controller method"""
        result = view_model.get_status_value("test_key")
        teensy_controller.get_status_value.assert_called_once_with("test_key")
        assert result == "test_value"
    
    def test_get_formatted_value(self, view_model, teensy_controller):
        """Test get_formatted_value calls controller method"""
        result = view_model.get_formatted_value("test_key")
        teensy_controller.get_formatted_value.assert_called_once_with("test_key")
        assert result == "formatted"
    
    # Test signal forwarding
    
    def test_status_changed_signal_forwarding(self, view_model, teensy_controller):
        """Test that status_changed signal is forwarded"""
        signal_emitted = [False]
        test_status = {'test': 'data'}
        received_status = [None]
        
        def on_signal(status):
            signal_emitted[0] = True
            received_status[0] = status
        
        view_model.status_changed.connect(on_signal)
        teensy_controller.status_changed.emit(test_status)
        
        assert signal_emitted[0]
        assert received_status[0] == test_status
    
    def test_connection_changed_signal_forwarding(self, view_model, teensy_controller):
        """Test that connection_changed signal is forwarded"""
        signal_emitted = [False]
        
        def on_signal(connected):
            signal_emitted[0] = True
        
        view_model.connection_changed.connect(on_signal)
        teensy_controller.connection_changed.emit(True)
        
        assert signal_emitted[0]
    
    def test_multiple_signal_forwarding(self, view_model, teensy_controller):
        """Test that multiple signals are forwarded correctly"""
        signals_emitted = {
            'spray_leveling': False,
            'auto_correction': False,
            'stability': False
        }
        
        view_model.spray_gun_leveling_changed.connect(
            lambda: signals_emitted.update({'spray_leveling': True}))
        view_model.auto_correction_enabled_changed.connect(
            lambda: signals_emitted.update({'auto_correction': True}))
        view_model.stability_enabled_changed.connect(
            lambda: signals_emitted.update({'stability': True}))
        
        # Emit signals from controller
        teensy_controller.spray_gun_leveling_changed.emit(True)
        teensy_controller.auto_correction_enabled_changed.emit(True)
        teensy_controller.stability_enabled_changed.emit(True)
        
        # All should be forwarded
        assert signals_emitted['spray_leveling']
        assert signals_emitted['auto_correction']
        assert signals_emitted['stability']
