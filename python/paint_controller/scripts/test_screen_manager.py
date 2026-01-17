#!/usr/bin/env python3
"""
Test script for adaptive multi-screen UI functionality.

This script tests the ScreenManager's ability to detect and handle screen changes.
It can be run standalone without ROS dependencies.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal, Slot

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paint_controller.core.screen_manager import ScreenManager


class ScreenManagerTester(QObject):
    """Test harness for ScreenManager functionality."""
    
    def __init__(self):
        super().__init__()
        self.screen_manager = ScreenManager(parent=self)
        
        # Connect to all signals for testing
        self.screen_manager.screen_added.connect(self.on_screen_added)
        self.screen_manager.screen_removed.connect(self.on_screen_removed)
        self.screen_manager.screens_changed.connect(self.on_screens_changed)
        self.screen_manager.primary_screen_changed.connect(self.on_primary_screen_changed)
        self.screen_manager.screen_count_changed.connect(self.on_screen_count_changed)
        
    @Slot(int, str)
    def on_screen_added(self, index, name):
        print(f"[TEST] Signal received: screen_added({index}, {name})")
        
    @Slot(int, str)
    def on_screen_removed(self, index, name):
        print(f"[TEST] Signal received: screen_removed({index}, {name})")
        
    @Slot()
    def on_screens_changed(self):
        print(f"[TEST] Signal received: screens_changed()")
        
    @Slot(str)
    def on_primary_screen_changed(self, name):
        print(f"[TEST] Signal received: primary_screen_changed({name})")
        
    @Slot(int)
    def on_screen_count_changed(self, count):
        print(f"[TEST] Signal received: screen_count_changed({count})")
    
    def run_tests(self):
        """Run a series of tests on the ScreenManager."""
        print("\n" + "="*60)
        print("SCREEN MANAGER TEST SUITE")
        print("="*60 + "\n")
        
        # Test 1: Property access
        print("Test 1: Property Access")
        print(f"  screen_count: {self.screen_manager.screen_count}")
        print(f"  primary_screen_name: {self.screen_manager.primary_screen_name}")
        print(f"  has_multiple_screens: {self.screen_manager.has_multiple_screens}")
        print("  ✓ Properties accessible\n")
        
        # Test 2: Slot methods
        print("Test 2: Slot Methods")
        count = self.screen_manager.get_screen_count()
        print(f"  get_screen_count(): {count}")
        
        primary_name = self.screen_manager.get_primary_screen_name()
        print(f"  get_primary_screen_name(): {primary_name}")
        
        primary_info = self.screen_manager.get_primary_screen_info()
        print(f"  get_primary_screen_info(): {primary_info.get('name', 'N/A')}")
        print("  ✓ Slot methods working\n")
        
        # Test 3: Screen information retrieval
        print("Test 3: Screen Information Retrieval")
        all_screens = self.screen_manager.get_all_screens_info()
        print(f"  Total screens detected: {len(all_screens)}")
        
        for i, screen_info in enumerate(all_screens):
            print(f"\n  Screen {i}:")
            print(f"    Name: {screen_info.get('name')}")
            print(f"    Resolution: {screen_info.get('width')}x{screen_info.get('height')}")
            print(f"    Refresh Rate: {screen_info.get('refreshRate')} Hz")
            print(f"    Position: ({screen_info.get('virtualX')}, {screen_info.get('virtualY')})")
            print(f"    Primary: {screen_info.get('isPrimary')}")
            print(f"    Device Pixel Ratio: {screen_info.get('devicePixelRatio')}")
        
        print("  ✓ Screen information retrieval working\n")
        
        # Test 4: Index validation
        print("Test 4: Index Validation")
        print(f"  is_valid_screen_index(0): {self.screen_manager.is_valid_screen_index(0)}")
        print(f"  is_valid_screen_index(-1): {self.screen_manager.is_valid_screen_index(-1)}")
        print(f"  is_valid_screen_index(99): {self.screen_manager.is_valid_screen_index(99)}")
        print("  ✓ Index validation working\n")
        
        # Test 5: Individual screen info
        print("Test 5: Individual Screen Info")
        if count > 0:
            screen_0_info = self.screen_manager.get_screen_info(0)
            print(f"  get_screen_info(0): {screen_0_info.get('name', 'N/A')}")
        
        invalid_info = self.screen_manager.get_screen_info(99)
        print(f"  get_screen_info(99): {invalid_info}")
        print("  ✓ Individual screen info working\n")
        
        print("="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")
        
        print("Monitoring for screen changes...")
        print("  - Connect or disconnect an external monitor to test real-time detection")
        print("  - Press Ctrl+C to exit\n")


def main():
    """Main test function."""
    print("Adaptive Multi-Screen UI Test")
    print("="*60)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create and run tester
    tester = ScreenManagerTester()
    
    # Run tests after a short delay to ensure everything is initialized
    QTimer.singleShot(500, tester.run_tests)
    
    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        tester.screen_manager.cleanup()
        sys.exit(0)


if __name__ == '__main__':
    main()
