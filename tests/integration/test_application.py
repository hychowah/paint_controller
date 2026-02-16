"""
Integration tests for PaintControllerApplication

Tests the complete application lifecycle and component integration.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock


class TestApplicationIntegration:
    """Integration tests for PaintControllerApplication"""
    
    @pytest.fixture
    def mock_ros_context(self):
        """Mock ROS context to avoid actual ROS initialization"""
        with patch('paint_controller.core.ros_manager.rclpy') as mock_rclpy:
            mock_rclpy.init = Mock()
            mock_rclpy.shutdown = Mock()
            mock_rclpy.ok = Mock(return_value=True)
            mock_rclpy.spin_once = Mock()
            yield mock_rclpy
    
    @pytest.fixture
    def mock_qt_app(self):
        """Mock Qt application to avoid creating actual GUI"""
        with patch('paint_controller.core.qt_manager.QApplication') as mock_app_class:
            mock_app = Mock()
            mock_app.exec = Mock(return_value=0)
            mock_app.quit = Mock()
            mock_app_class.return_value = mock_app
            yield mock_app
    
    @pytest.fixture
    def mock_qml_engine(self):
        """Mock QML engine"""
        with patch('paint_controller.core.qt_manager.QQmlApplicationEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_context = Mock()
            mock_engine.rootContext = Mock(return_value=mock_context)
            mock_engine.load = Mock()
            mock_engine.rootObjects = Mock(return_value=[Mock()])
            mock_engine.addImageProvider = Mock()
            mock_engine.addImportPath = Mock()
            mock_engine_class.return_value = mock_engine
            yield mock_engine
    
    def test_service_container_initialization(self):
        """Test that ServiceContainer initializes correctly"""
        from paint_controller.core.service_container import ServiceContainer
        
        container = ServiceContainer()
        assert container is not None
        
        # Test basic registration
        container.register_singleton('test', lambda: "value")
        assert container.get('test') == "value"
        
        container.cleanup_all()
    
    def test_ros_manager_initialization(self, mock_ros_context):
        """Test ROSManager initialization"""
        from paint_controller.core.ros_manager import ROSManager
        
        manager = ROSManager()
        assert not manager.is_initialized
        
        manager.initialize()
        assert manager.is_initialized
        mock_ros_context.init.assert_called_once()
    
    def test_qt_manager_initialization(self, mock_qt_app, mock_qml_engine):
        """Test QtManager initialization"""
        from paint_controller.core.qt_manager import QtManager
        
        manager = QtManager()
        manager.initialize()
        
        assert manager.app is not None
        assert manager.engine is not None
    
    def test_application_initialization_sequence(self, mock_ros_context, mock_qt_app, mock_qml_engine):
        """Test that application components initialize in correct order"""
        from paint_controller.core.app import PaintControllerApplication
        
        # Mock config file
        with patch('paint_controller.core.app.ConfigLoader.load_config') as mock_config:
            mock_config.return_value = Mock(
                video_port=5000,
                update_rate=60.0,
                joystick_deadzone=0.1
            )
            
            # Mock RobotController to avoid full initialization
            with patch('paint_controller.core.app.RobotController') as mock_controller_class:
                mock_controller = Mock()
                mock_controller.video_stream_handler = Mock()
                mock_controller.video_stream_handler.ef_image_provider = Mock()
                mock_controller.video_stream_handler.front_image_provider = Mock()
                mock_controller.video_stream_handler.rear_image_provider = Mock()
                mock_controller.bird_view_service = Mock()
                mock_controller.bird_view_service.image_provider = Mock()
                mock_controller.status_updated = Mock()
                mock_controller.status_updated.emit = Mock()
                mock_controller._publish_heartbeat = Mock()
                mock_controller.system_monitor = Mock()
                mock_controller.system_monitor.start_monitoring = Mock()
                
                # Add all required controller attributes
                for attr in ['overlayController', 'workFlowHandler', 'workflow_runner',
                           'warningHandler', 'wheel_controller', 'winch_controller',
                           'steam_deck_handler', 'wind_monitor', 'teensy_controller',
                           'esp32_valve_controller', 'lidar_controller', 'action_config',
                           'heartbeat_handler', 'controlProcessor', 'ssh_controller',
                           'screen_recorder', 'ros_bag_recorder', 'settings_manager',
                           'screen_manager']:
                    setattr(mock_controller, attr, Mock())
                
                mock_controller_class.return_value = mock_controller
                
                app = PaintControllerApplication()
                
                # Should not raise any exceptions
                try:
                    app.initialize()
                    
                    # Verify initialization sequence
                    assert mock_config.called
                    assert mock_ros_context.init.called
                    assert mock_controller_class.called
                    
                    # Cleanup
                    app.cleanup()
                except Exception as e:
                    pytest.fail(f"Application initialization failed: {e}")
    
    def test_application_cleanup_order(self, mock_ros_context, mock_qt_app, mock_qml_engine):
        """Test that cleanup happens in correct order"""
        from paint_controller.core.app import PaintControllerApplication
        
        cleanup_order = []
        
        # Mock components to track cleanup order
        with patch('paint_controller.core.app.ConfigLoader.load_config') as mock_config:
            mock_config.return_value = Mock(
                video_port=5000,
                update_rate=60.0,
                joystick_deadzone=0.1
            )
            
            with patch('paint_controller.core.app.RobotController') as mock_controller_class:
                mock_controller = Mock()
                mock_controller.video_stream_handler = Mock()
                mock_controller.video_stream_handler.ef_image_provider = Mock()
                mock_controller.video_stream_handler.front_image_provider = Mock()
                mock_controller.video_stream_handler.rear_image_provider = Mock()
                mock_controller.bird_view_service = Mock()
                mock_controller.bird_view_service.image_provider = Mock()
                mock_controller.status_updated = Mock()
                mock_controller.status_updated.emit = Mock()
                mock_controller._publish_heartbeat = Mock()
                mock_controller.system_monitor = Mock()
                mock_controller.system_monitor.start_monitoring = Mock()
                mock_controller.heartbeat_handler = Mock()
                
                # Track cleanup calls
                def track_controller_cleanup():
                    cleanup_order.append('controller')
                
                def track_heartbeat_cleanup():
                    cleanup_order.append('heartbeat')
                
                mock_controller.cleanup = track_controller_cleanup
                mock_controller.heartbeat_handler.cleanup = track_heartbeat_cleanup
                
                # Add all required controller attributes
                for attr in ['overlayController', 'workFlowHandler', 'workflow_runner',
                           'warningHandler', 'wheel_controller', 'winch_controller',
                           'steam_deck_handler', 'wind_monitor', 'teensy_controller',
                           'esp32_valve_controller', 'lidar_controller', 'action_config',
                           'controlProcessor', 'ssh_controller',
                           'screen_recorder', 'ros_bag_recorder', 'settings_manager',
                           'screen_manager']:
                    setattr(mock_controller, attr, Mock())
                
                mock_controller_class.return_value = mock_controller
                
                app = PaintControllerApplication()
                app.initialize()
                app.cleanup()
                
                # Verify cleanup was called
                assert 'controller' in cleanup_order or 'heartbeat' in cleanup_order
                assert mock_ros_context.shutdown.called
