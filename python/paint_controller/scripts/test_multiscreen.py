#!/usr/bin/env python3
"""
Simple test script for ScreenManager functionality

This script tests the screen detection and monitoring capabilities
without requiring the full Paint Controller application.
"""

import sys

from PySide6.QtWidgets import QApplication

from paint_controller.services.screen_manager import ScreenManager


def on_screens_changed():
    """Handle screens changed signal"""
    print("\n[EVENT] Screen configuration changed!")
    print(f"Current screen count: {screen_manager.get_screen_count()}")
    print_screen_info()


def on_screen_added(index):
    """Handle screen added signal"""
    print(f"\n[EVENT] Screen added at index {index}")
    print(f"Screen info: {screen_manager.get_screen_info_string(index)}")


def on_screen_removed(index):
    """Handle screen removed signal"""
    print(f"\n[EVENT] Screen removed at index {index}")


def on_primary_changed(name):
    """Handle primary screen changed signal"""
    print(f"\n[EVENT] Primary screen changed to: {name}")


def print_screen_info():
    """Print information about all detected screens"""
    screen_count = screen_manager.get_screen_count()
    print(f"\n{'=' * 60}")
    print(f"Detected {screen_count} screen(s):")
    print(f"{'=' * 60}")

    for i in range(screen_count):
        info = screen_manager.get_screen_info_string(i)
        print(f"  {info}")

    print(f"{'=' * 60}")
    print(f"Primary screen: {screen_manager.get_primary_screen_name()}")
    print(f"{'=' * 60}\n")


def main():
    """Main test function"""
    global screen_manager

    print("ScreenManager Test - Multi-Screen Display Support")
    print("=" * 60)
    print("This script monitors screen changes in real-time.")
    print("Try connecting or disconnecting external monitors.")
    print("Press Ctrl+C to exit.")
    print("=" * 60)

    # Create Qt application
    app = QApplication(sys.argv)

    # Create screen manager
    screen_manager = ScreenManager()

    # Connect signals
    screen_manager.screens_changed.connect(on_screens_changed)
    screen_manager.screen_added.connect(on_screen_added)
    screen_manager.screen_removed.connect(on_screen_removed)
    screen_manager.primary_screen_changed.connect(on_primary_changed)

    # Print initial screen info
    print("\nInitial screen configuration:")
    print_screen_info()

    # Print detailed info for all screens
    print("Detailed screen information:")
    print("-" * 60)
    screens = screen_manager.get_screen_list()
    for screen_dict in screens:
        print(f"\nScreen {screen_dict['index']}:")
        for key, value in screen_dict.items():
            if key != "index":
                print(f"  {key}: {value}")
    print("-" * 60)

    print("\nMonitoring for changes... (Press Ctrl+C to exit)")

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
