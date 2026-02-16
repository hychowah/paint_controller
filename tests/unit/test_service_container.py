"""
Unit tests for ServiceContainer

Tests service registration, retrieval, lifecycle management, and cleanup.

Note: This test imports the ServiceContainer module directly to avoid ROS dependencies.
"""

import pytest
import sys
from pathlib import Path

# Add paint_controller to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'python'))

# Import the module directly, not through package
import importlib.util
spec = importlib.util.spec_from_file_location(
    "service_container",
    Path(__file__).parent.parent.parent / 'python' / 'paint_controller' / 'core' / 'service_container.py'
)
service_container = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service_container)

ServiceContainer = service_container.ServiceContainer
ServiceLifetime = service_container.ServiceLifetime


class TestServiceContainer:
    """Test cases for ServiceContainer"""
    
    def test_register_singleton(self, service_container):
        """Test singleton service registration and retrieval"""
        # Create a simple service class
        class TestService:
            def __init__(self):
                self.value = 42
        
        # Register as singleton
        service_container.register_singleton('test_service', lambda: TestService())
        
        # Get service twice
        service1 = service_container.get('test_service')
        service2 = service_container.get('test_service')
        
        # Should be the same instance
        assert service1 is service2
        assert service1.value == 42
    
    def test_register_transient(self, service_container):
        """Test transient service registration and retrieval"""
        call_count = [0]
        
        class TestService:
            def __init__(self):
                call_count[0] += 1
                self.instance_id = call_count[0]
        
        # Register as transient
        service_container.register('test_service', lambda: TestService())
        
        # Get service twice
        service1 = service_container.get('test_service')
        service2 = service_container.get('test_service')
        
        # Should be different instances
        assert service1 is not service2
        assert service1.instance_id == 1
        assert service2.instance_id == 2
    
    def test_duplicate_registration_fails(self, service_container):
        """Test that registering the same service twice raises an error"""
        service_container.register_singleton('test', lambda: object())
        
        with pytest.raises(ValueError, match="already registered"):
            service_container.register_singleton('test', lambda: object())
    
    def test_get_unregistered_service_fails(self, service_container):
        """Test that getting an unregistered service raises KeyError"""
        with pytest.raises(KeyError, match="not registered"):
            service_container.get('nonexistent')
    
    def test_try_get_returns_none(self, service_container):
        """Test that try_get returns None for unregistered service"""
        result = service_container.try_get('nonexistent')
        assert result is None
    
    def test_try_get_returns_service(self, service_container):
        """Test that try_get returns service if registered"""
        service_container.register_singleton('test', lambda: 'value')
        result = service_container.try_get('test')
        assert result == 'value'
    
    def test_has_service(self, service_container):
        """Test has() method"""
        assert not service_container.has('test')
        
        service_container.register_singleton('test', lambda: object())
        assert service_container.has('test')
    
    def test_cleanup_calls_service_cleanup(self, service_container):
        """Test that cleanup_all() calls cleanup() on services"""
        cleanup_called = [False]
        
        class TestService:
            def cleanup(self):
                cleanup_called[0] = True
        
        service_container.register_singleton('test', lambda: TestService())
        service_container.get('test')  # Create the instance
        
        service_container.cleanup_all()
        assert cleanup_called[0]
    
    def test_cleanup_reverse_order(self, service_container):
        """Test that cleanup happens in reverse creation order"""
        cleanup_order = []
        
        class ServiceA:
            def cleanup(self):
                cleanup_order.append('A')
        
        class ServiceB:
            def cleanup(self):
                cleanup_order.append('B')
        
        class ServiceC:
            def cleanup(self):
                cleanup_order.append('C')
        
        # Register and create services in order A, B, C
        service_container.register_singleton('a', lambda: ServiceA())
        service_container.register_singleton('b', lambda: ServiceB())
        service_container.register_singleton('c', lambda: ServiceC())
        
        service_a = service_container.get('a')
        service_b = service_container.get('b')
        service_c = service_container.get('c')
        
        # Cleanup should happen in reverse order: C, B, A
        service_container.cleanup_all()
        assert cleanup_order == ['C', 'B', 'A']
        
        # Verify instances are cleared
        # Re-getting should create new instances (not same as before)
        service_a2 = service_container.get('a')
        assert service_a2 is not service_a  # New instance after cleanup
    
    def test_cleanup_handles_exceptions(self, service_container):
        """Test that cleanup continues even if one service fails"""
        cleanup_called = [False, False]
        
        class ServiceA:
            def cleanup(self):
                cleanup_called[0] = True
                raise Exception("Cleanup failed")
        
        class ServiceB:
            def cleanup(self):
                cleanup_called[1] = True
        
        service_container.register_singleton('a', lambda: ServiceA())
        service_container.register_singleton('b', lambda: ServiceB())
        
        service_container.get('a')
        service_container.get('b')
        
        # Should not raise, should cleanup both
        service_container.cleanup_all()
        assert cleanup_called[0]
        assert cleanup_called[1]
    
    def test_clear_removes_all_services(self, service_container):
        """Test that clear() removes all service registrations"""
        service_container.register_singleton('test1', lambda: object())
        service_container.register_singleton('test2', lambda: object())
        
        assert service_container.has('test1')
        assert service_container.has('test2')
        
        service_container.clear()
        
        assert not service_container.has('test1')
        assert not service_container.has('test2')
    
    def test_dependency_injection_pattern(self, service_container):
        """Test typical dependency injection usage pattern"""
        class DatabaseService:
            def get_data(self):
                return "data from db"
        
        class BusinessService:
            def __init__(self, db):
                self.db = db
            
            def process(self):
                return f"processed: {self.db.get_data()}"
        
        # Register services with dependencies
        service_container.register_singleton('db', lambda: DatabaseService())
        service_container.register_singleton('business', 
            lambda: BusinessService(service_container.get('db')))
        
        # Get business service (which depends on db service)
        business = service_container.get('business')
        result = business.process()
        
        assert result == "processed: data from db"
        
        # Verify they're singletons
        business2 = service_container.get('business')
        assert business is business2
