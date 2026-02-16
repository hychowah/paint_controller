#!/usr/bin/env python3
"""
Service Container for Dependency Injection

Provides a lightweight dependency injection container for managing service
lifecycles and dependencies in the paint_controller application.
"""

from typing import Dict, Callable, Any, Optional, TypeVar, List
from dataclasses import dataclass
from enum import Enum


class ServiceLifetime(Enum):
    """Service lifetime management options"""
    SINGLETON = "singleton"  # Single instance shared across all requests
    TRANSIENT = "transient"  # New instance created for each request


@dataclass
class ServiceDescriptor:
    """Describes how a service should be created and managed"""
    name: str
    factory: Callable[[], Any]
    lifetime: ServiceLifetime
    instance: Optional[Any] = None


T = TypeVar('T')


class ServiceContainer:
    """
    Dependency Injection Container
    
    Manages service registration, creation, and lifecycle.
    Supports both singleton and transient services with automatic cleanup.
    
    Example:
        container = ServiceContainer()
        
        # Register singleton service
        container.register_singleton('settings', lambda: SettingsManager())
        
        # Register transient service
        container.register('logger', lambda: Logger())
        
        # Get service
        settings = container.get('settings')
        
        # Cleanup all services
        container.cleanup_all()
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._creation_order: List[str] = []  # Track order for cleanup
        
    def register_singleton(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register a singleton service.
        
        The factory function will be called once on first access, and the
        instance will be reused for all subsequent requests.
        
        Args:
            name: Unique service name
            factory: Factory function that creates the service instance
        """
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered")
        
        self._services[name] = ServiceDescriptor(
            name=name,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON,
            instance=None
        )
    
    def register(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register a transient service.
        
        The factory function will be called every time the service is requested,
        creating a new instance each time.
        
        Args:
            name: Unique service name
            factory: Factory function that creates the service instance
        """
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered")
        
        self._services[name] = ServiceDescriptor(
            name=name,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT,
            instance=None
        )
    
    def get(self, name: str) -> Any:
        """
        Get a service instance by name.
        
        For singleton services, creates the instance on first access and
        returns the same instance for all subsequent calls.
        
        For transient services, creates a new instance every time.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        if name not in self._services:
            raise KeyError(f"Service '{name}' is not registered")
        
        descriptor = self._services[name]
        
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if descriptor.instance is None:
                # Create singleton instance on first access
                descriptor.instance = descriptor.factory()
                self._creation_order.append(name)
            return descriptor.instance
        else:
            # Create new instance for transient services
            instance = descriptor.factory()
            self._creation_order.append(name)
            return instance
    
    def try_get(self, name: str) -> Optional[Any]:
        """
        Try to get a service instance, returning None if not registered.
        
        Args:
            name: Service name
            
        Returns:
            Service instance or None if not registered
        """
        try:
            return self.get(name)
        except KeyError:
            return None
    
    def has(self, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: Service name
            
        Returns:
            True if service is registered, False otherwise
        """
        return name in self._services
    
    def cleanup_all(self) -> None:
        """
        Cleanup all services in reverse creation order.
        
        Calls cleanup() method on each service instance if it exists,
        working backwards through the creation order to properly handle
        dependencies.
        """
        # Cleanup in reverse order of creation
        for name in reversed(self._creation_order):
            if name not in self._services:
                continue
            
            descriptor = self._services[name]
            if descriptor.instance is None:
                continue
            
            # Try to call cleanup if the service has one
            if hasattr(descriptor.instance, 'cleanup'):
                try:
                    descriptor.instance.cleanup()
                except Exception as e:
                    print(f"Error cleaning up service '{name}': {e}")
            
            # Clear the instance
            descriptor.instance = None
        
        # Clear creation order
        self._creation_order.clear()
    
    def clear(self) -> None:
        """
        Clear all service registrations.
        
        Note: Does not call cleanup(). Call cleanup_all() first if needed.
        """
        self._services.clear()
        self._creation_order.clear()
