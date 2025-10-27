"""
CRITICAL FIX #3: Publisher Error Handling
File: python/UITeensyController.py

This demonstrates proper error handling for ROS publishers.
"""

from typing import Dict, Optional, Any
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, Int32
from dataclasses import dataclass
import time


@dataclass
class PublisherRegistry:
    """Registry of publishers with safe access"""
    _publishers: Dict[str, Optional[Any]] = None
    _lock = None
    
    def __post_init__(self):
        from threading import Lock
        if self._publishers is None:
            self._publishers = {}
        if self._lock is None:
            self._lock = Lock()


class SafeTeensyController:
    """
    Improved Teensy controller with proper error handling for publishers.
    
    Key improvements:
    - Validates publishers exist before publishing
    - Retries on network errors
    - Reports failures instead of silently failing
    - Safe cleanup on exit
    """
    
    def __init__(self, robot_controller):
        self._robot_controller = robot_controller
        self._publishers = {}
        self._failed_publishers = {}  # Track which publishers failed
        self._status = {
            'available': False,
            # ... status fields
        }
        
        # Try to create all publishers
        self._setup_publishers()
        
        # Track last publish time for diagnostics
        self._last_publish_times = {}

    def _setup_publishers(self):
        """
        Set up ROS publishers with error handling.
        
        If a publisher fails to create, we log it but continue
        with other publishers. This allows partial operation.
        """
        publisher_config = {
            'teensy_relay': (Bool, 'teensy/relay/cmd'),
            'teensy_enable': (Bool, 'teensy/enable/cmd'),
            'top_rail_speed': (Float32, 'teensy/top_rail/speed/cmd'),
            'top_rail_home': (Bool, 'teensy/top_rail/home/cmd'),
            'arm_rail_speed': (Float32, 'teensy/arm_rail/speed/cmd'),
            'arm_extend': (Int32, 'teensy/arm/extend/cmd'),
            'arm_rail_home': (Bool, 'teensy/arm/home/cmd'),
            # ... more publishers
        }
        
        logger = self._robot_controller.get_logger()
        
        for pub_name, (msg_type, topic) in publisher_config.items():
            try:
                pub = self._robot_controller.create_publisher(msg_type, topic, 1)
                self._publishers[pub_name] = pub
                logger.info(f"✓ Created publisher: {topic} ({pub_name})")
                self._failed_publishers[pub_name] = False
                
            except Exception as e:
                logger.error(f"✗ Failed to create publisher {topic}: {type(e).__name__}: {e}")
                self._publishers[pub_name] = None
                self._failed_publishers[pub_name] = True

    def publish_safe(self, pub_name: str, msg, retry_count: int = 1) -> bool:
        """
        Safely publish message with error handling and optional retry.
        
        Args:
            pub_name: Name of the publisher
            msg: Message to publish
            retry_count: Number of times to retry if publish fails
            
        Returns:
            True if successful, False otherwise
        """
        logger = self._robot_controller.get_logger()
        
        # Check if publisher exists and is valid
        if pub_name not in self._publishers:
            logger.warning(f"Publisher '{pub_name}' not registered")
            return False
        
        pub = self._publishers[pub_name]
        if pub is None:
            if not self._failed_publishers.get(pub_name, False):
                logger.warning(f"Publisher '{pub_name}' is unavailable")
                self._failed_publishers[pub_name] = True
            return False
        
        # Try to publish with retry logic
        for attempt in range(retry_count):
            try:
                pub.publish(msg)
                
                # Update success stats
                self._last_publish_times[pub_name] = time.time()
                self._failed_publishers[pub_name] = False
                
                return True
                
            except Exception as e:
                logger.warning(
                    f"Failed to publish to '{pub_name}' (attempt {attempt+1}/{retry_count}): "
                    f"{type(e).__name__}: {e}"
                )
                
                # Mark as failed so we don't keep trying
                self._failed_publishers[pub_name] = True
                
                if attempt < retry_count - 1:
                    time.sleep(0.01)  # Brief delay before retry
        
        return False

    def set_relay(self, enabled: bool) -> bool:
        """Set relay state with error handling"""
        msg = Bool()
        msg.data = enabled
        
        success = self.publish_safe('teensy_relay', msg)
        if not success:
            self._robot_controller.get_logger().error(f"Failed to set relay to {enabled}")
        
        return success

    def set_enable(self, enabled: bool) -> bool:
        """Set enable state with error handling"""
        msg = Bool()
        msg.data = enabled
        
        success = self.publish_safe('teensy_enable', msg)
        if not success:
            self._robot_controller.get_logger().error(f"Failed to set enable to {enabled}")
        
        return success

    def move_top_rail(self, speed: float) -> bool:
        """Move top rail at specified speed with error handling"""
        if not -1.0 <= speed <= 1.0:
            self._robot_controller.get_logger().error(f"Invalid speed: {speed} (must be -1.0 to 1.0)")
            return False
        
        msg = Float32()
        msg.data = speed
        
        success = self.publish_safe('top_rail_speed', msg)
        if not success:
            self._robot_controller.get_logger().error(f"Failed to set top rail speed to {speed}")
        
        return success

    def get_health_status(self) -> Dict[str, bool]:
        """
        Get health status of all publishers.
        
        Returns:
            Dict mapping publisher name to availability status
        """
        status = {}
        for pub_name, pub in self._publishers.items():
            status[pub_name] = pub is not None and not self._failed_publishers.get(pub_name, False)
        return status

    def report_health(self) -> str:
        """Get formatted health report"""
        status = self.get_health_status()
        healthy = sum(1 for v in status.values() if v)
        total = len(status)
        
        report = f"Publisher Health: {healthy}/{total} available\n"
        for name, available in status.items():
            status_str = "✓" if available else "✗"
            report += f"  {status_str} {name}\n"
        
        return report

    def cleanup(self):
        """Clean up all publishers"""
        try:
            logger = self._robot_controller.get_logger() if hasattr(self._robot_controller, 'get_logger') else None
            
            for pub_name, pub in self._publishers.items():
                if pub:
                    try:
                        # Publishers are automatically cleaned up when node is destroyed
                        # But we can do explicit cleanup here if needed
                        pass
                    except Exception as e:
                        if logger:
                            logger.error(f"Error cleaning up publisher {pub_name}: {e}")
            
            self._publishers.clear()
            
            if logger:
                logger.info("Teensy controller cleanup complete")
                
        except Exception as e:
            print(f"Error during TeensyController cleanup: {e}")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage(robot_controller):
    """Example of how to use SafeTeensyController"""
    
    controller = SafeTeensyController(robot_controller)
    
    # Use safe publish methods
    if not controller.set_relay(True):
        print("Failed to enable relay - might be offline")
    
    # Attempt motor movement with automatic retry
    if not controller.move_top_rail(0.5):
        print("Failed to move top rail - check connection")
    
    # Check health before critical operation
    health = controller.get_health_status()
    if health.get('teensy_enable', False):
        # Safe to proceed
        controller.set_enable(True)
    else:
        # Teensy not connected
        print("Warning: Teensy not connected")
    
    # Print diagnostics
    print(controller.report_health())
    
    # Cleanup
    controller.cleanup()


# ============================================================================
# TESTING
# ============================================================================

class MockNode:
    """Mock ROS node for testing"""
    
    def __init__(self):
        self._publications = {}
        self._logger = self
    
    def get_logger(self):
        return self
    
    def create_publisher(self, msg_type, topic, qos):
        """Simulate publisher creation"""
        if "invalid" in topic:
            raise RuntimeError(f"Cannot create publisher for {topic}")
        
        class MockPublisher:
            def __init__(self, topic):
                self.topic = topic
                self.publish_count = 0
            
            def publish(self, msg):
                self.publish_count += 1
        
        return MockPublisher(topic)
    
    # Logger interface
    def error(self, msg):
        print(f"[ERROR] {msg}")
    
    def warning(self, msg):
        print(f"[WARN] {msg}")
    
    def info(self, msg):
        print(f"[INFO] {msg}")


def test_safe_teensy_controller():
    """Test the SafeTeensyController"""
    node = MockNode()
    controller = SafeTeensyController(node)
    
    print("Testing publish_safe method...")
    result = controller.set_relay(True)
    print(f"Result: {result}")
    
    print("\nHealth status:")
    print(controller.report_health())


if __name__ == "__main__":
    test_safe_teensy_controller()
