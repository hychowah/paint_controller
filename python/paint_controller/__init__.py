"""Paint Controller - ROS 2 Robot Control System with PySide6 UI.

This package provides a comprehensive control system for a painting robot,
including hardware controllers, event handlers, video streaming, workflow
management, and a Qt/QML-based user interface.

Package Structure:
    controllers/    - Hardware and system controllers (lidar, wheel, winch, etc.)
    handlers/       - Event and input handlers (emergency, heartbeat, steam_deck, etc.)
    services/       - Service modules (video_stream, workflow management)
    ui/             - UI-specific controllers (overlay)
    core/           - Core application (main controller, settings)
    models/         - Data models and configuration
    widgets/        - Custom Qt widgets (VTK visualization)
    scripts/        - Standalone diagnostic and test scripts
    config/         - Configuration files (JSON)
    workflow/       - Workflow definitions (YAML)

Backward Compatibility:
    For compatibility with existing code, old module names are re-exported below.
    These will be deprecated in a future release. Please update your imports to use
    the new package structure:
        OLD: from UILidarController import LidarController
        NEW: from paint_controller.controllers.lidar import LidarController
"""

# ============================================================================
# Backward Compatibility Layer
# ============================================================================
# These imports maintain compatibility with old import paths.
# They will be deprecated in a future release.

# Controllers (old names prefixed with 'UI')
from .controllers.lidar import LidarController as UILidarController
from .controllers.wheel import WheelController as UIWheelController
from .controllers.winch import WinchController as UIWinchController
from .controllers.teensy import TeensyController as UITeensyController
from .controllers.wind_monitor import WindMonitor as UIWindMonitor
from .controllers.system_monitor import SystemMonitor as UISystemMonitor
from .controllers.system_monitor import SystemMonitorWorker
from .controllers.ssh import UISSHController, SSHLauncher

# Handlers (old names prefixed with 'UI')
from .handlers.emergency import EmergencyButtonHandler as UIEmergencyButtonHandler
from .handlers.heartbeat import UIHeartbeatHandler, HeartbeatStatus
from .handlers.input import UIInputHandler
from .handlers.warnings import WarningHandler
from .handlers.steam_deck import SteamDeckHandler as UISteamDeckHandler
from .handlers.control_processor import ControlProcessor as UIControlProcessor
from .handlers.control_processor import ControlConfig

# Services
from .services.video_stream import VideoStreamHandler, CameraStream, ImageProvider
from .services.workflow_legacy import WorkFlowHandler, ActionWorker

# UI
from .ui.overlay import OverlayController

# Core
from .core.application import RosThread, main
from .core.settings import SettingsManager

# Models
from .models.action_config import ActionConfigPython

# Widgets
from .widgets.vtk_pointcloud import VTKPointCloudWidget

# Workflow (already properly namespaced)
from .services.workflow.workflow_runner import WorkFlowRunner

# ============================================================================
# New API - Recommended Imports
# ============================================================================
# Subpackages are available for organized imports:
#   paint_controller.controllers.*
#   paint_controller.handlers.*
#   paint_controller.services.*
#   paint_controller.ui.*
#   paint_controller.core.*
#   paint_controller.models.*
#   paint_controller.widgets.*

__version__ = '0.1.0'

__all__ = [
    # Backward compatibility - Controllers
    'UILidarController',
    'UIWheelController',
    'UIWinchController',
    'UITeensyController',
    'UIWindMonitor',
    'UISystemMonitor',
    'SystemMonitorWorker',
    'UISSHController',
    'SSHLauncher',
    
    # Backward compatibility - Handlers
    'UIEmergencyButtonHandler',
    'UIHeartbeatHandler',
    'HeartbeatStatus',
    'UIInputHandler',
    'WarningHandler',
    'UISteamDeckHandler',
    'UIControlProcessor',
    'ControlConfig',
    
    # Services
    'VideoStreamHandler',
    'CameraStream',
    'ImageProvider',
    'WorkFlowHandler',
    'ActionWorker',
    'WorkFlowRunner',
    
    # UI
    'OverlayController',
    
    # Core
    'RosThread',
    'SettingsManager',
    'main',
    
    # Models
    'ActionConfigPython',
    
    # Widgets
    'VTKPointCloudWidget',
]
