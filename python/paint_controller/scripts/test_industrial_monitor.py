#!/usr/bin/env python3
"""
Test script for Industrial Monitor UI
Run this script to check if the industrial monitor QML files load correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtWidgets import QApplication
    
    def test_industrial_monitor():
        """Test loading the industrial monitor QML file"""
        print("Testing Industrial Monitor UI...")
        
        app = QApplication(sys.argv)
        engine = QQmlApplicationEngine()
        
        # Path to the QML file
        qml_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            'qml',
            'pages',
            'status',
            'PageIndustrialMonitor.qml'
        )
        
        print(f"Loading QML from: {qml_file}")
        
        if not os.path.exists(qml_file):
            print(f"❌ ERROR: QML file not found: {qml_file}")
            return False
        
        # Try to load the QML
        engine.load(QUrl.fromLocalFile(qml_file))
        
        if not engine.rootObjects():
            print("❌ ERROR: Failed to load QML file")
            return False
        
        print("✅ QML file loaded successfully!")
        print("✅ Industrial Monitor UI is ready")
        
        # Don't actually show the window, just test loading
        return True
    
    if __name__ == '__main__':
        success = test_industrial_monitor()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"⚠️  PySide6 not available: {e}")
    print("This is expected in CI environment.")
    print("Run this test on actual hardware with PySide6 installed.")
    print("\nTo install PySide6:")
    print("  pip install PySide6")
    sys.exit(0)
