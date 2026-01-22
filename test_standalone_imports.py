#!/usr/bin/env python3
"""
Test script to verify that paint_controller can be imported without ROS.
This validates the mock system works correctly.
"""

import sys

def test_ros_mock():
    """Test that ros_mock module works"""
    print("=" * 60)
    print("Testing ROS Mock Module")
    print("=" * 60)
    
    try:
        from paint_controller.core import ros_mock
        print("✓ ros_mock module imported successfully")
        
        # Test creating mock node
        node = ros_mock.MockNode("test_node")
        print(f"✓ Created mock node: {node.node_name}")
        
        # Test creating mock publisher
        pub = node.create_publisher(ros_mock.MockFloat32, "/test/topic", 10)
        print(f"✓ Created mock publisher: {pub.topic}")
        
        # Test publishing
        msg = ros_mock.MockFloat32(data=42.0)
        pub.publish(msg)
        print(f"✓ Published mock message with data: {msg.data}")
        
        # Test mock subscription
        def callback(msg):
            pass
        sub = node.create_subscription(ros_mock.MockFloat32, "/test/sub", callback, 10)
        print(f"✓ Created mock subscription: {sub.topic}")
        
        # Test other mock functions
        ros_mock.mock_init()
        print("✓ mock_init() works")
        
        result = ros_mock.mock_ok()
        print(f"✓ mock_ok() returns: {result}")
        
        ros_mock.mock_spin_once(node)
        print("✓ mock_spin_once() works")
        
        ros_mock.mock_shutdown()
        print("✓ mock_shutdown() works")
        
        node.destroy_node()
        print("✓ Mock node destroyed")
        
        return True
    except Exception as e:
        print(f"✗ Error testing ros_mock: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optional_imports():
    """Test that controllers can be imported without ROS"""
    print("\n" + "=" * 60)
    print("Testing Optional ROS Imports")
    print("=" * 60)
    
    modules_to_test = [
        'paint_controller.controllers.teensy',
        'paint_controller.controllers.wheel',
        'paint_controller.controllers.winch',
        'paint_controller.controllers.wind_monitor',
        'paint_controller.controllers.lidar',
        'paint_controller.handlers.heartbeat',
        'paint_controller.handlers.control_processor',
        'paint_controller.services.workflow_legacy',
    ]
    
    all_passed = True
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            # If it's a PySide6 or other non-ROS import error, that's expected in headless env
            if 'PySide6' in str(e) or 'gi.repository' in str(e) or 'paramiko' in str(e):
                print(f"⊘ {module_name} (needs GUI/extra deps - expected in CI)")
            else:
                print(f"✗ {module_name}: {e}")
                all_passed = False
        except Exception as e:
            print(f"✗ {module_name}: {e}")
            all_passed = False
    
    return all_passed

def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Paint Controller Standalone Mode Test" + " " * 11 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Check if ROS is available
    try:
        import rclpy
        print("⚠ WARNING: ROS2 (rclpy) is available - mock won't be used")
        print("   To test standalone mode, run in environment without ROS")
        print()
    except ImportError:
        print("✓ ROS2 not available - perfect for testing standalone mode")
        print()
    
    # Run tests
    test1_passed = test_ros_mock()
    test2_passed = test_optional_imports()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"ROS Mock Module: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Optional Imports: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    print()
    
    if test1_passed and test2_passed:
        print("✓ ALL TESTS PASSED - Standalone mode is working!")
        return 0
    else:
        print("✗ SOME TESTS FAILED - See errors above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
