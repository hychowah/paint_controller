#!/usr/bin/env python3
"""
Screen Manager for Multi-Display Support

Handles detection and management of multiple screens/displays with real-time monitoring.
Provides signals for screen changes to enable adaptive UI behavior.
"""

from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from PySide6.QtGui import QGuiApplication, QScreen


class ScreenInfo:
    """Information about a detected screen/display"""
    
    def __init__(self, screen: QScreen, index: int):
        self.index = index
        self.name = screen.name()
        self.manufacturer = screen.manufacturer()
        self.model = screen.model()
        self.serial_number = screen.serialNumber()
        self.width = screen.size().width()
        self.height = screen.size().height()
        self.refresh_rate = screen.refreshRate()
        self.virtual_x = screen.geometry().x()
        self.virtual_y = screen.geometry().y()
        self.is_primary = (screen == QGuiApplication.primaryScreen())
        self.device_pixel_ratio = screen.devicePixelRatio()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert screen info to dictionary"""
        return {
            'index': self.index,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'width': self.width,
            'height': self.height,
            'refresh_rate': self.refresh_rate,
            'virtual_x': self.virtual_x,
            'virtual_y': self.virtual_y,
            'is_primary': self.is_primary,
            'device_pixel_ratio': self.device_pixel_ratio,
        }
    
    def __str__(self) -> str:
        """String representation of screen info"""
        primary_str = " (Primary)" if self.is_primary else ""
        return (f"Screen {self.index}{primary_str}: {self.name} - "
                f"{self.width}x{self.height} @ {self.refresh_rate}Hz")


class ScreenManager(QObject):
    """
    Manages multiple displays with real-time detection
    
    Signals:
        screens_changed: Emitted when screens are added/removed
        screen_added: Emitted when a new screen is detected
        screen_removed: Emitted when a screen is disconnected
        primary_screen_changed: Emitted when primary screen changes
    """
    
    # Configuration constants
    MONITOR_INTERVAL_MS = 1000  # Polling interval for screen changes (milliseconds)
    
    screens_changed = Signal()
    screen_added = Signal(int)  # screen index
    screen_removed = Signal(int)  # screen index
    primary_screen_changed = Signal(str)  # screen name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._screens: List[QScreen] = []
        self._screen_count = 0
        self._primary_screen_name = ""
        
        # Monitor for screen changes
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._check_screen_changes)
        self._monitor_timer.start(self.MONITOR_INTERVAL_MS)
        
        # Initial detection
        self._detect_screens()
        
        # Connect to Qt screen signals
        app = QGuiApplication.instance()
        if app:
            app.screenAdded.connect(self._on_screen_added)
            app.screenRemoved.connect(self._on_screen_removed)
            app.primaryScreenChanged.connect(self._on_primary_screen_changed)
    
    def _log_info(self, message: str) -> None:
        """Helper method for logging that checks if logger is available"""
        if hasattr(self, 'node') and hasattr(self.node, 'get_logger'):
            self.node.get_logger().info(message)
    
    def _detect_screens(self) -> None:
        """Detect all available screens"""
        app = QGuiApplication.instance()
        if not app:
            return
        
        self._screens = app.screens()
        self._screen_count = len(self._screens)
        
        primary = app.primaryScreen()
        if primary:
            self._primary_screen_name = primary.name()
        
        self._log_info(f'Detected {self._screen_count} screen(s)')
        for i, screen in enumerate(self._screens):
            info = ScreenInfo(screen, i)
            self._log_info(f'  {info}')
    
    def _check_screen_changes(self) -> None:
        """Periodic check for screen configuration changes"""
        app = QGuiApplication.instance()
        if not app:
            return
        
        current_screens = app.screens()
        current_count = len(current_screens)
        
        # Check if screen count changed
        if current_count != self._screen_count:
            self._log_info(f'Screen count changed: {self._screen_count} -> {current_count}')
            
            self._screen_count = current_count
            self._screens = current_screens
            self.screens_changed.emit()
    
    @Slot(QScreen)
    def _on_screen_added(self, screen: QScreen) -> None:
        """Handle screen added event"""
        self._detect_screens()
        index = self._screens.index(screen) if screen in self._screens else -1
        
        info = ScreenInfo(screen, index)
        self._log_info(f'Screen added: {info}')
        
        if index >= 0:
            self.screen_added.emit(index)
        self.screens_changed.emit()
    
    @Slot(QScreen)
    def _on_screen_removed(self, screen: QScreen) -> None:
        """Handle screen removed event"""
        # Get index before it's removed
        index = self._screens.index(screen) if screen in self._screens else -1
        
        self._log_info(f'Screen removed: {screen.name()} (index {index})')
        
        self._detect_screens()
        
        if index >= 0:
            self.screen_removed.emit(index)
        self.screens_changed.emit()
    
    @Slot(QScreen)
    def _on_primary_screen_changed(self, screen: QScreen) -> None:
        """Handle primary screen change"""
        if screen:
            old_name = self._primary_screen_name
            self._primary_screen_name = screen.name()
            
            self._log_info(f'Primary screen changed: {old_name} -> {self._primary_screen_name}')
            
            self.primary_screen_changed.emit(self._primary_screen_name)
    
    @Slot(result=int)
    def get_screen_count(self) -> int:
        """Get the number of detected screens"""
        return self._screen_count
    
    @Slot(result=list)
    def get_screen_list(self) -> List[Dict[str, Any]]:
        """Get list of all screens with their information"""
        screen_list = []
        for i, screen in enumerate(self._screens):
            info = ScreenInfo(screen, i)
            screen_list.append(info.to_dict())
        return screen_list
    
    @Slot(int, result=str)
    def get_screen_info_string(self, index: int) -> str:
        """Get formatted string with screen information"""
        if 0 <= index < len(self._screens):
            info = ScreenInfo(self._screens[index], index)
            return str(info)
        return f"Screen {index}: Not available"
    
    @Slot(result=str)
    def get_primary_screen_name(self) -> str:
        """Get the name of the primary screen"""
        return self._primary_screen_name
    
    def get_screen(self, index: int) -> Optional[QScreen]:
        """Get QScreen object by index"""
        if 0 <= index < len(self._screens):
            return self._screens[index]
        return None
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self._monitor_timer:
            self._monitor_timer.stop()
