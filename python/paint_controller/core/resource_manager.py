#!/usr/bin/env python3
"""
Resource Management Utilities

Provides utilities for proper resource management including context managers
and automatic cleanup tracking.
"""

from typing import Optional, Any, List
from abc import ABC, abstractmethod


class ManagedResource(ABC):
    """
    Base class for resources that need explicit cleanup.
    
    Provides a standard interface for resources that need to be properly
    cleaned up when no longer needed. Can be used as a context manager.
    
    Example:
        class MyResource(ManagedResource):
            def _initialize(self):
                self.connection = open_connection()
                
            def _cleanup(self):
                self.connection.close()
        
        with MyResource() as resource:
            resource.do_work()
        # cleanup() called automatically
    """
    
    def __init__(self):
        self._initialized = False
        self._cleaned_up = False
    
    def __enter__(self):
        """Context manager entry"""
        if not self._initialized:
            self._initialize()
            self._initialized = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.cleanup()
        return False
    
    @abstractmethod
    def _initialize(self) -> None:
        """
        Initialize the resource.
        
        Override this method to implement resource initialization logic.
        """
        pass
    
    @abstractmethod
    def _cleanup(self) -> None:
        """
        Cleanup the resource.
        
        Override this method to implement resource cleanup logic.
        """
        pass
    
    def cleanup(self) -> None:
        """
        Public cleanup method that can be called manually.
        
        Safe to call multiple times - cleanup only happens once.
        """
        if not self._cleaned_up:
            self._cleaned_up = True
            self._cleanup()


class ResourceTracker:
    """
    Tracks multiple resources and ensures they are all cleaned up.
    
    Useful for managing multiple resources that need to be cleaned up
    in reverse order of creation.
    
    Example:
        tracker = ResourceTracker()
        resource1 = tracker.track(Resource1())
        resource2 = tracker.track(Resource2())
        
        # Later...
        tracker.cleanup_all()  # Cleans up resource2, then resource1
    """
    
    def __init__(self):
        self._resources: List[Any] = []
    
    def track(self, resource: Any) -> Any:
        """
        Track a resource for cleanup.
        
        Args:
            resource: Resource to track (should have cleanup() method)
            
        Returns:
            The resource (for convenience)
        """
        self._resources.append(resource)
        return resource
    
    def cleanup_all(self) -> None:
        """
        Cleanup all tracked resources in reverse order.
        
        Continues cleanup even if individual cleanups fail.
        """
        # Cleanup in reverse order
        for resource in reversed(self._resources):
            if hasattr(resource, 'cleanup'):
                try:
                    resource.cleanup()
                except Exception as e:
                    print(f"Error cleaning up resource {resource}: {e}")
        
        self._resources.clear()
    
    def clear(self) -> None:
        """
        Clear tracked resources without cleanup.
        
        Use cleanup_all() if you want to cleanup resources before clearing.
        """
        self._resources.clear()
