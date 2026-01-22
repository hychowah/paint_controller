"""
Mock ROS2 interfaces for standalone (non-ROS) mode.

This module provides lightweight mock implementations of ROS2 classes
when rclpy is not available, allowing the UI to run without ROS installed.
"""

from typing import Any, Callable, Optional
import logging


class MockNode:
    """Mock ROS2 Node for standalone mode"""
    
    def __init__(self, node_name: str):
        self.node_name = node_name
        self._logger = logging.getLogger(node_name)
        self._publishers = {}
        self._subscriptions = {}
        self._services = {}
        self._clients = {}
        
    def get_logger(self):
        """Return Python logger as mock ROS logger"""
        return self._logger
    
    def create_publisher(self, msg_type, topic: str, qos_profile):
        """Create mock publisher that does nothing"""
        publisher = MockPublisher(topic, msg_type)
        self._publishers[topic] = publisher
        self._logger.debug(f"Created mock publisher: {topic}")
        return publisher
    
    def create_subscription(self, msg_type, topic: str, callback: Callable, qos_profile):
        """Create mock subscription that never receives messages"""
        subscription = MockSubscription(topic, msg_type, callback)
        self._subscriptions[topic] = subscription
        self._logger.debug(f"Created mock subscription: {topic}")
        return subscription
    
    def create_service(self, srv_type, srv_name: str, callback: Callable):
        """Create mock service that never receives requests"""
        service = MockService(srv_name, srv_type, callback)
        self._services[srv_name] = service
        self._logger.debug(f"Created mock service: {srv_name}")
        return service
    
    def create_client(self, srv_type, srv_name: str):
        """Create mock client that always fails"""
        client = MockClient(srv_name, srv_type)
        self._clients[srv_name] = client
        self._logger.debug(f"Created mock client: {srv_name}")
        return client
    
    def destroy_node(self):
        """Mock node destruction"""
        self._logger.debug(f"Mock node {self.node_name} destroyed")
        self._publishers.clear()
        self._subscriptions.clear()
        self._services.clear()
        self._clients.clear()


class MockPublisher:
    """Mock ROS2 Publisher"""
    
    def __init__(self, topic: str, msg_type):
        self.topic = topic
        self.msg_type = msg_type
        self._logger = logging.getLogger(f"MockPublisher.{topic}")
    
    def publish(self, msg):
        """Mock publish - logs but doesn't send"""
        self._logger.debug(f"Mock publish to {self.topic}: {msg}")


class MockSubscription:
    """Mock ROS2 Subscription"""
    
    def __init__(self, topic: str, msg_type, callback: Callable):
        self.topic = topic
        self.msg_type = msg_type
        self.callback = callback
        self._logger = logging.getLogger(f"MockSubscription.{topic}")


class MockService:
    """Mock ROS2 Service"""
    
    def __init__(self, service_name: str, srv_type, callback: Callable):
        self.service_name = service_name
        self.srv_type = srv_type
        self.callback = callback
        self._logger = logging.getLogger(f"MockService.{service_name}")


class MockClient:
    """Mock ROS2 Client"""
    
    def __init__(self, service_name: str, srv_type):
        self.service_name = service_name
        self.srv_type = srv_type
        self._logger = logging.getLogger(f"MockClient.{service_name}")
    
    def call_async(self, request):
        """Mock async call - always fails"""
        self._logger.warning(f"Mock client call to {self.service_name} - not implemented in standalone mode")
        # Return a mock future that's already done and has no result
        from concurrent.futures import Future
        future = Future()
        future.set_exception(RuntimeError("ROS not available in standalone mode"))
        return future


class MockClock:
    """Mock ROS2 Clock"""
    
    def now(self):
        """Return mock time"""
        return MockTime()


class MockTime:
    """Mock ROS2 Time"""
    
    def __init__(self):
        import time
        self.nanoseconds = int(time.time() * 1e9)
    
    def to_msg(self):
        """Convert to ROS message format"""
        # Return a simple dict-like object
        return type('TimeMsg', (), {'sec': self.nanoseconds // 1000000000, 'nanosec': self.nanoseconds % 1000000000})()


# Mock message types
class MockUInt8:
    """Mock std_msgs/UInt8"""
    def __init__(self, data: int = 0):
        self.data = data


class MockBool:
    """Mock std_msgs/Bool"""
    def __init__(self, data: bool = False):
        self.data = data


class MockFloat32:
    """Mock std_msgs/Float32"""
    def __init__(self, data: float = 0.0):
        self.data = data


class MockFloat64:
    """Mock std_msgs/Float64"""
    def __init__(self, data: float = 0.0):
        self.data = data


class MockInt32:
    """Mock std_msgs/Int32"""
    def __init__(self, data: int = 0):
        self.data = data


class MockString:
    """Mock std_msgs/String"""
    def __init__(self, data: str = ""):
        self.data = data


class MockEmpty:
    """Mock std_msgs/Empty"""
    pass


class MockTwist:
    """Mock geometry_msgs/Twist"""
    def __init__(self):
        self.linear = MockVector3()
        self.angular = MockVector3()


class MockVector3:
    """Mock geometry_msgs/Vector3"""
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


class MockFloat32MultiArray:
    """Mock std_msgs/Float32MultiArray"""
    def __init__(self):
        self.data = []


class MockInt32MultiArray:
    """Mock std_msgs/Int32MultiArray"""
    def __init__(self):
        self.data = []


def mock_ok() -> bool:
    """Mock rclpy.ok() - always returns True in standalone mode"""
    return True


def mock_spin_once(node, timeout_sec: float = None):
    """Mock rclpy.spin_once() - does nothing in standalone mode"""
    pass


def mock_init(args=None):
    """Mock rclpy.init() - does nothing in standalone mode"""
    logging.info("ROS mock initialized - running in standalone mode")


def mock_shutdown():
    """Mock rclpy.shutdown() - does nothing in standalone mode"""
    logging.info("ROS mock shutdown - standalone mode")


if __name__ == '__main__':
    # Simple test when run directly
    print("Testing ROS Mock Module")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Test creating mock node
    node = MockNode("test_node")
    print(f"✓ Created mock node: {node.node_name}")
    
    # Test creating mock publisher
    pub = node.create_publisher(MockFloat32, "/test/topic", 10)
    print(f"✓ Created mock publisher: {pub.topic}")
    
    # Test publishing
    msg = MockFloat32(data=42.0)
    pub.publish(msg)
    print(f"✓ Published mock message with data: {msg.data}")
    
    # Test mock subscription
    def callback(msg):
        pass
    sub = node.create_subscription(MockFloat32, "/test/sub", callback, 10)
    print(f"✓ Created mock subscription: {sub.topic}")
    
    # Test other mock functions
    mock_init()
    print("✓ mock_init() works")
    
    result = mock_ok()
    print(f"✓ mock_ok() returns: {result}")
    
    mock_spin_once(node)
    print("✓ mock_spin_once() works")
    
    mock_shutdown()
    print("✓ mock_shutdown() works")
    
    node.destroy_node()
    print("✓ Mock node destroyed")
    
    print()
    print("✅ All mock functionality works correctly!")

