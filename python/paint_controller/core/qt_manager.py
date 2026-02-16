#!/usr/bin/env python3
"""
Qt Manager

Encapsulates Qt/QML application lifecycle and setup.
"""

import sys
import os
from typing import Dict, Any, Optional
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication


class QtManager:
    """
    Manages Qt application and QML engine lifecycle.
    
    Encapsulates Qt/QML initialization, context property registration,
    and cleanup to separate concerns from the main application.
    
    Example:
        manager = QtManager()
        manager.initialize()
        manager.register_context_property("backend", controller)
        manager.load_qml("path/to/main.qml")
        exit_code = manager.exec()
        manager.cleanup()
    """
    
    def __init__(self):
        self._app: Optional[QApplication] = None
        self._engine: Optional[QQmlApplicationEngine] = None
        self._timers: Dict[str, QTimer] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """
        Initialize Qt application.
        
        Creates QApplication instance and QML engine.
        Must be called before any other Qt operations.
        """
        if self._initialized:
            return
        
        # Create Qt application
        self._app = QApplication(sys.argv)
        
        # Create QML engine
        self._engine = QQmlApplicationEngine()
        
        self._initialized = True
        print("Qt application initialized")
    
    def register_context_property(self, name: str, value: Any) -> None:
        """
        Register a context property for QML.
        
        Args:
            name: Property name to use in QML
            value: Python object to expose to QML
        """
        if not self._initialized:
            raise RuntimeError("QtManager not initialized. Call initialize() first.")
        
        self._engine.rootContext().setContextProperty(name, value)
    
    def register_multiple_context_properties(self, properties: Dict[str, Any]) -> None:
        """
        Register multiple context properties at once.
        
        Args:
            properties: Dictionary of name -> value pairs
        """
        for name, value in properties.items():
            self.register_context_property(name, value)
    
    def add_image_provider(self, provider_id: str, provider: Any) -> None:
        """
        Add an image provider to the QML engine.
        
        Args:
            provider_id: ID to use in QML (e.g., "image://provider_id/...")
            provider: QQuickImageProvider instance
        """
        if not self._initialized:
            raise RuntimeError("QtManager not initialized. Call initialize() first.")
        
        self._engine.addImageProvider(provider_id, provider)
    
    def add_import_path(self, path: str) -> None:
        """
        Add a QML import path.
        
        Args:
            path: Directory path containing QML modules
        """
        if not self._initialized:
            raise RuntimeError("QtManager not initialized. Call initialize() first.")
        
        self._engine.addImportPath(path)
    
    def load_qml(self, qml_path: str) -> bool:
        """
        Load QML file.
        
        Args:
            qml_path: Path to QML file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("QtManager not initialized. Call initialize() first.")
        
        url = QUrl.fromLocalFile(qml_path)
        self._engine.load(url)
        
        # Check if loading was successful
        root_objects = self._engine.rootObjects()
        if not root_objects:
            print(f"ERROR: Failed to load QML from {qml_path}")
            return False
        
        print(f"QML loaded from {qml_path}")
        return True
    
    def create_timer(self, name: str, interval_ms: int, callback) -> QTimer:
        """
        Create and register a QTimer.
        
        Args:
            name: Unique timer name (for tracking)
            interval_ms: Timer interval in milliseconds
            callback: Function to call on timeout
            
        Returns:
            Created QTimer instance
        """
        timer = QTimer()
        timer.timeout.connect(callback)
        timer.start(interval_ms)
        self._timers[name] = timer
        return timer
    
    def stop_all_timers(self) -> None:
        """Stop all registered timers."""
        for name, timer in self._timers.items():
            try:
                timer.stop()
            except Exception as e:
                print(f"Error stopping timer '{name}': {e}")
        self._timers.clear()
    
    def exec(self) -> int:
        """
        Execute Qt application event loop.
        
        Blocks until the application exits.
        
        Returns:
            Application exit code
        """
        if not self._initialized:
            raise RuntimeError("QtManager not initialized. Call initialize() first.")
        
        return self._app.exec()
    
    def quit(self) -> None:
        """Request application quit."""
        if self._app:
            self._app.quit()
    
    def cleanup(self) -> None:
        """
        Cleanup Qt resources.
        
        Stops all timers and cleans up Qt objects.
        Should be called before application exit.
        """
        # Stop all timers
        self.stop_all_timers()
        
        # Cleanup QML engine
        if self._engine:
            # Clear root context properties to break references
            try:
                # Engine cleanup happens automatically via Qt parent/child relationships
                pass
            except Exception as e:
                print(f"Error during engine cleanup: {e}")
        
        self._initialized = False
        print("Qt application cleaned up")
    
    @property
    def app(self) -> QApplication:
        """Get QApplication instance"""
        return self._app
    
    @property
    def engine(self) -> QQmlApplicationEngine:
        """Get QML engine instance"""
        return self._engine
