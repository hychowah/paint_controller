#!/usr/bin/env python3
"""
Screen Manager for adaptive multi-screen UI support.

Monitors connected displays and handles dynamic screen changes in real-time.
Provides Qt signals for screen addition/removal and exposes screen information to QML.
"""

from typing import List, Dict, Optional
from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QScreen


class ScreenInfo:
    """Information about a single screen/display."""
    
    def __init__(self, screen: QScreen, index: int):
        """
        Initialize screen information.
        
        Args:
            screen: Qt QScreen object
            index: Screen index in the system
        """
        self.screen = screen
        self.index = index
        self.name = screen.name()
        self.width = screen.size().width()
        self.height = screen.size().height()
        self.virtual_x = screen.virtualGeometry().x()
        self.virtual_y = screen.virtualGeometry().y()
        self.refresh_rate = screen.refreshRate()
        self.is_primary = (screen == QApplication.primaryScreen())
        self.device_pixel_ratio = screen.devicePixelRatio()
    
    def to_dict(self) -> Dict:
        """Convert screen info to dictionary for QML."""
        return {
            'index': self.index,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'virtualX': self.virtual_x,
            'virtualY': self.virtual_y,
            'refreshRate': self.refresh_rate,
            'isPrimary': self.is_primary,
            'devicePixelRatio': self.device_pixel_ratio
        }
    
    def __str__(self) -> str:
        """String representation of screen info."""
        primary_str = " (PRIMARY)" if self.is_primary else ""
        return (f"Screen {self.index}: {self.name}{primary_str} - "
                f"{self.width}x{self.height} @ {self.refresh_rate}Hz "
                f"at ({self.virtual_x}, {self.virtual_y})")


class ScreenManager(QObject):
    """
    Manager for handling multi-screen displays and screen changes.
    
    Monitors screen addition/removal and provides real-time information
    about connected displays to the Qt/QML application.
    """
    
    # Signals for screen changes
    screen_added = Signal(int, str)  # index, name
    screen_removed = Signal(int, str)  # index, name
    screens_changed = Signal()  # General notification
    primary_screen_changed = Signal(str)  # new primary screen name
    screen_count_changed = Signal(int)  # new screen count
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the screen manager.
        
        Args:
            parent: Parent QObject (typically the main application controller)
        """
        super().__init__(parent)
        
        # Get the QApplication instance
        self._app = QApplication.instance()
        if not self._app:
            raise RuntimeError("QApplication instance not found. "
                             "ScreenManager must be created after QApplication.")
        
        # Track current screens
        self._screens: List[ScreenInfo] = []
        self._screen_count = 0
        self._primary_screen_name = ""
        
        # Connect to Qt's screen management signals
        self._app.screenAdded.connect(self._on_screen_added)
        self._app.screenRemoved.connect(self._on_screen_removed)
        self._app.primaryScreenChanged.connect(self._on_primary_screen_changed)
        
        # Initialize screen list
        self._update_screen_list()
        
        print(f"ScreenManager initialized with {self._screen_count} screen(s)")
        self._log_screen_info()
    
    def _update_screen_list(self):
        """Update the internal list of screens."""
        qt_screens = self._app.screens()
        self._screens = [ScreenInfo(screen, idx) for idx, screen in enumerate(qt_screens)]
        self._screen_count = len(self._screens)
        
        # Update primary screen name
        primary = self._app.primaryScreen()
        self._primary_screen_name = primary.name() if primary else ""
    
    def _log_screen_info(self):
        """Log information about all connected screens."""
        print("\n=== Connected Screens ===")
        for screen_info in self._screens:
            print(f"  {screen_info}")
        print(f"Total: {self._screen_count} screen(s)\n")
    
    def _on_screen_added(self, screen: QScreen):
        """
        Handle screen addition event.
        
        Args:
            screen: The newly added QScreen
        """
        # Update screen list
        old_count = self._screen_count
        self._update_screen_list()
        
        # Find the new screen info
        screen_name = screen.name()
        screen_index = -1
        for info in self._screens:
            if info.screen == screen:
                screen_index = info.index
                break
        
        print(f"✓ Screen added: {screen_name} (index {screen_index})")
        print(f"  Resolution: {screen.size().width()}x{screen.size().height()}")
        print(f"  Position: ({screen.virtualGeometry().x()}, {screen.virtualGeometry().y()})")
        
        # Emit signals
        self.screen_added.emit(screen_index, screen_name)
        self.screen_count_changed.emit(self._screen_count)
        self.screens_changed.emit()
        
        # Log all screens
        self._log_screen_info()
    
    def _on_screen_removed(self, screen: QScreen):
        """
        Handle screen removal event.
        
        Args:
            screen: The removed QScreen
        """
        screen_name = screen.name()
        
        # Try to find the screen index before removal
        screen_index = -1
        for info in self._screens:
            if info.screen == screen:
                screen_index = info.index
                break
        
        print(f"✗ Screen removed: {screen_name} (index {screen_index})")
        
        # Update screen list
        old_count = self._screen_count
        self._update_screen_list()
        
        # Emit signals
        self.screen_removed.emit(screen_index, screen_name)
        self.screen_count_changed.emit(self._screen_count)
        self.screens_changed.emit()
        
        # Log remaining screens
        self._log_screen_info()
    
    def _on_primary_screen_changed(self, screen: QScreen):
        """
        Handle primary screen change event.
        
        Args:
            screen: The new primary screen
        """
        if screen:
            old_primary = self._primary_screen_name
            new_primary = screen.name()
            self._primary_screen_name = new_primary
            
            print(f"→ Primary screen changed: {old_primary} → {new_primary}")
            
            # Update screen list to reflect new primary status
            self._update_screen_list()
            
            # Emit signals
            self.primary_screen_changed.emit(new_primary)
            self.screens_changed.emit()
    
    # Properties exposed to QML
    @Property(int, notify=screen_count_changed)
    def screen_count(self) -> int:
        """Get the number of connected screens."""
        return self._screen_count
    
    @Property(str, notify=primary_screen_changed)
    def primary_screen_name(self) -> str:
        """Get the name of the primary screen."""
        return self._primary_screen_name
    
    @Property(bool, notify=screens_changed)
    def has_multiple_screens(self) -> bool:
        """Check if there are multiple screens connected."""
        return self._screen_count > 1
    
    # Slots for QML interaction
    @Slot(result=int)
    def get_screen_count(self) -> int:
        """Get the current number of screens (callable from QML)."""
        return self._screen_count
    
    @Slot(int, result='QVariantMap')
    def get_screen_info(self, index: int) -> Dict:
        """
        Get information about a specific screen.
        
        Args:
            index: Screen index
            
        Returns:
            Dictionary with screen information, or empty dict if invalid index
        """
        if 0 <= index < len(self._screens):
            return self._screens[index].to_dict()
        return {}
    
    @Slot(result='QVariantList')
    def get_all_screens_info(self) -> List[Dict]:
        """
        Get information about all connected screens.
        
        Returns:
            List of dictionaries with screen information
        """
        return [info.to_dict() for info in self._screens]
    
    @Slot(result=str)
    def get_primary_screen_name(self) -> str:
        """Get the name of the primary screen (callable from QML)."""
        return self._primary_screen_name
    
    @Slot(result='QVariantMap')
    def get_primary_screen_info(self) -> Dict:
        """
        Get information about the primary screen.
        
        Returns:
            Dictionary with primary screen information
        """
        for info in self._screens:
            if info.is_primary:
                return info.to_dict()
        return {}
    
    @Slot(int, result=bool)
    def is_valid_screen_index(self, index: int) -> bool:
        """
        Check if a screen index is valid.
        
        Args:
            index: Screen index to check
            
        Returns:
            True if the index is valid, False otherwise
        """
        return 0 <= index < self._screen_count
    
    def cleanup(self):
        """Cleanup resources when shutting down."""
        try:
            # Disconnect signals
            if self._app:
                self._app.screenAdded.disconnect(self._on_screen_added)
                self._app.screenRemoved.disconnect(self._on_screen_removed)
                self._app.primaryScreenChanged.disconnect(self._on_primary_screen_changed)
            
            print("ScreenManager cleanup complete")
        except Exception as e:
            print(f"Error during ScreenManager cleanup: {e}")
