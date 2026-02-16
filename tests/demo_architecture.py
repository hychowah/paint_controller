#!/usr/bin/env python3
"""
Simple demo to test the new architecture components without ROS.

This demonstrates that the new ServiceContainer and architecture
work independently and can be tested in isolation.
"""

import sys
from pathlib import Path

# Add paint_controller to path
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir / 'python'))

# Import only the components we need
import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

base_path = base_dir / 'python' / 'paint_controller' / 'core'

# Load modules
service_container_module = load_module('service_container', base_path / 'service_container.py')
resource_manager_module = load_module('resource_manager', base_path / 'resource_manager.py')

ServiceContainer = service_container_module.ServiceContainer
ResourceTracker = resource_manager_module.ResourceTracker


def demo_service_container():
    """Demo ServiceContainer functionality"""
    print("\n=== ServiceContainer Demo ===\n")
    
    # Create container
    container = ServiceContainer()
    print("✓ Created ServiceContainer")
    
    # Define some example services
    class DatabaseService:
        def __init__(self):
            self.connection = "Connected to DB"
            print("  → DatabaseService initialized")
        
        def query(self, sql):
            return f"Query result for: {sql}"
        
        def cleanup(self):
            print("  → DatabaseService cleaned up")
    
    class CacheService:
        def __init__(self, db):
            self.db = db
            self.cache = {}
            print("  → CacheService initialized (with DB dependency)")
        
        def get(self, key):
            if key in self.cache:
                return self.cache[key]
            result = self.db.query(f"SELECT * FROM items WHERE id={key}")
            self.cache[key] = result
            return result
        
        def cleanup(self):
            print("  → CacheService cleaned up")
    
    # Register services
    print("\nRegistering services...")
    container.register_singleton('database', lambda: DatabaseService())
    container.register_singleton('cache', 
        lambda: CacheService(container.get('database')))
    print("✓ Services registered")
    
    # Use services
    print("\nUsing services...")
    cache = container.get('cache')
    result = cache.get(42)
    print(f"  Cache result: {result}")
    
    # Get same instance (singleton)
    cache2 = container.get('cache')
    print(f"  Same instance? {cache is cache2}")
    
    # Cleanup
    print("\nCleaning up...")
    container.cleanup_all()
    print("✓ Cleanup complete")


def demo_resource_tracker():
    """Demo ResourceTracker functionality"""
    print("\n=== ResourceTracker Demo ===\n")
    
    class ManagedFile:
        def __init__(self, filename):
            self.filename = filename
            print(f"  → Opened {filename}")
        
        def cleanup(self):
            print(f"  → Closed {self.filename}")
    
    # Create tracker
    tracker = ResourceTracker()
    print("✓ Created ResourceTracker")
    
    # Track resources
    print("\nTracking resources...")
    file1 = tracker.track(ManagedFile("data1.txt"))
    file2 = tracker.track(ManagedFile("data2.txt"))
    file3 = tracker.track(ManagedFile("data3.txt"))
    print("✓ Resources tracked")
    
    # Cleanup in reverse order
    print("\nCleaning up (reverse order)...")
    tracker.cleanup_all()
    print("✓ Cleanup complete")


def demo_dependency_injection():
    """Demo dependency injection pattern"""
    print("\n=== Dependency Injection Demo ===\n")
    
    # Create container
    container = ServiceContainer()
    
    class ConfigService:
        def __init__(self):
            self.settings = {'max_speed': 100, 'timeout': 30}
            print("  → ConfigService initialized")
    
    class LoggerService:
        def __init__(self):
            self.logs = []
            print("  → LoggerService initialized")
        
        def log(self, message):
            self.logs.append(message)
            print(f"  [LOG] {message}")
    
    class MotorController:
        def __init__(self, config, logger):
            self.config = config
            self.logger = logger
            self.speed = 0
            logger.log("MotorController initialized")
        
        def set_speed(self, speed):
            max_speed = self.config.settings['max_speed']
            if speed > max_speed:
                self.logger.log(f"Speed {speed} exceeds max {max_speed}, clamping")
                speed = max_speed
            self.speed = speed
            self.logger.log(f"Speed set to {speed}")
            return self.speed
    
    # Register services with dependencies
    print("Registering services...")
    container.register_singleton('config', lambda: ConfigService())
    container.register_singleton('logger', lambda: LoggerService())
    container.register_singleton('motor',
        lambda: MotorController(
            container.get('config'),
            container.get('logger')
        ))
    print("✓ Services registered\n")
    
    # Use motor controller (automatically gets dependencies)
    print("Using motor controller...")
    motor = container.get('motor')
    motor.set_speed(50)
    motor.set_speed(150)  # Will be clamped
    
    print("\n✓ Demo complete")
    container.cleanup_all()


if __name__ == '__main__':
    print("=" * 60)
    print("Paint Controller Architecture Demo")
    print("=" * 60)
    
    try:
        demo_service_container()
        demo_resource_tracker()
        demo_dependency_injection()
        
        print("\n" + "=" * 60)
        print("✓ All demos completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
