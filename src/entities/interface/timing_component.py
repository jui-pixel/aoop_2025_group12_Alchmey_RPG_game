"""
Timing Component Interface
Handles lifetime management, timeouts, and temporal effects.
"""

from typing import Optional, Callable, List
from .entity_interface import ComponentInterface


class TimingComponent(ComponentInterface):
    """
    Timing component that handles all time-related functionality:
    - Lifetime management
    - Timeout handling
    - Periodic updates
    - Time-based effects
    """
    
    def __init__(self, entity: 'EntityInterface'):
        super().__init__(entity)
        self.lifetime: float = -1.0  # -1 means infinite lifetime
        self.age: float = 0.0  # Current age of the entity
        self.timeout_callbacks: List[tuple] = []  # List of (time, callback) tuples
        self.periodic_callbacks: List[tuple] = []  # List of (interval, callback, last_call) tuples
        self.is_alive: bool = True
        self.destroy_callback: Optional[Callable] = None
    
    def init(self) -> None:
        """Initialize timing component."""
        self.age = 0.0
        self.is_alive = True
        self.timeout_callbacks = []
        self.periodic_callbacks = []
    
    def update(self, dt: float, current_time: float) -> None:
        """Update timing component and handle time-based events."""
        if not self.is_alive:
            return
        
        self.age += dt
        
        # Check lifetime
        if self.lifetime > 0 and self.age >= self.lifetime:
            self.destroy()
            return
        
        # Handle timeout callbacks
        self._update_timeout_callbacks(dt, current_time)
        
        # Handle periodic callbacks
        self._update_periodic_callbacks(dt, current_time)
    
    def set_lifetime(self, lifetime: float) -> None:
        """Set the lifetime of the entity in seconds."""
        self.lifetime = lifetime
    
    def get_remaining_lifetime(self) -> float:
        """Get remaining lifetime in seconds."""
        if self.lifetime <= 0:
            return -1.0  # Infinite
        return max(0.0, self.lifetime - self.age)
    
    def get_age(self) -> float:
        """Get current age of the entity."""
        return self.age
    
    def add_timeout(self, delay: float, callback: Callable) -> None:
        """
        Add a timeout callback that will be called after a delay.
        Args:
            delay: Delay in seconds
            callback: Function to call
        """
        self.timeout_callbacks.append((delay, callback))
    
    def add_periodic(self, interval: float, callback: Callable) -> None:
        """
        Add a periodic callback that will be called at regular intervals.
        Args:
            interval: Interval in seconds
            callback: Function to call
        """
        self.periodic_callbacks.append((interval, callback, 0.0))
    
    def remove_timeout(self, callback: Callable) -> bool:
        """Remove a timeout callback. Returns True if found and removed."""
        for i, (delay, cb) in enumerate(self.timeout_callbacks):
            if cb == callback:
                self.timeout_callbacks.pop(i)
                return True
        return False
    
    def remove_periodic(self, callback: Callable) -> bool:
        """Remove a periodic callback. Returns True if found and removed."""
        for i, (interval, cb, last_call) in enumerate(self.periodic_callbacks):
            if cb == callback:
                self.periodic_callbacks.pop(i)
                return True
        return False
    
    def set_destroy_callback(self, callback: Callable) -> None:
        """Set callback to be called when entity is destroyed."""
        self.destroy_callback = callback
    
    def destroy(self) -> None:
        """Destroy the entity and call destroy callback."""
        if not self.is_alive:
            return
        
        self.is_alive = False
        
        # Call destroy callback
        if self.destroy_callback:
            try:
                self.destroy_callback(self.entity)
            except Exception as e:
                print(f"Error in destroy callback: {e}")
        
        # Mark entity for removal (this would be handled by the game system)
        if hasattr(self.entity, 'kill'):
            self.entity.kill()
        
        print(f"Entity {self.entity.__class__.__name__} destroyed (age: {self.age:.2f}s)")
    
    def is_expired(self) -> bool:
        """Check if entity has expired (lifetime reached)."""
        return self.lifetime > 0 and self.age >= self.lifetime
    
    def reset_age(self) -> None:
        """Reset the age of the entity."""
        self.age = 0.0
    
    def extend_lifetime(self, additional_time: float) -> None:
        """Extend the lifetime by additional time."""
        if self.lifetime > 0:
            self.lifetime += additional_time
    
    def _update_timeout_callbacks(self, dt: float, current_time: float) -> None:
        """Update and execute timeout callbacks."""
        for i in range(len(self.timeout_callbacks) - 1, -1, -1):
            delay, callback = self.timeout_callbacks[i]
            delay -= dt
            
            if delay <= 0:
                # Execute callback
                try:
                    callback(self.entity)
                except Exception as e:
                    print(f"Error in timeout callback: {e}")
                
                # Remove callback
                self.timeout_callbacks.pop(i)
            else:
                # Update delay
                self.timeout_callbacks[i] = (delay, callback)
    
    def _update_periodic_callbacks(self, dt: float, current_time: float) -> None:
        """Update and execute periodic callbacks."""
        for i in range(len(self.periodic_callbacks)):
            interval, callback, last_call = self.periodic_callbacks[i]
            last_call += dt
            
            if last_call >= interval:
                # Execute callback
                try:
                    callback(self.entity)
                except Exception as e:
                    print(f"Error in periodic callback: {e}")
                
                # Reset last call time
                self.periodic_callbacks[i] = (interval, callback, 0.0)
            else:
                # Update last call time
                self.periodic_callbacks[i] = (interval, callback, last_call)
    
    def get_timeout_count(self) -> int:
        """Get number of active timeout callbacks."""
        return len(self.timeout_callbacks)
    
    def get_periodic_count(self) -> int:
        """Get number of active periodic callbacks."""
        return len(self.periodic_callbacks)
    
    def clear_all_callbacks(self) -> None:
        """Clear all timeout and periodic callbacks."""
        self.timeout_callbacks.clear()
        self.periodic_callbacks.clear()
    
    def pause(self) -> None:
        """Pause the timing component (stop aging)."""
        # This would be implemented if pause functionality is needed
        pass
    
    def resume(self) -> None:
        """Resume the timing component (resume aging)."""
        # This would be implemented if pause functionality is needed
        pass
