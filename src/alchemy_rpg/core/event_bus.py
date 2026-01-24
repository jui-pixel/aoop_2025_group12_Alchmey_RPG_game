from typing import Callable, Dict, List, Any

class EventBus:
    """
    Central event bus for decoupling systems.
    Allows UI, ECS, and Core systems to communicate via events.
    """
    def __init__(self):
        self.listeners: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Subscribe a callback to an event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        if callback not in self.listeners[event_type]:
            self.listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]):
        """Unsubscribe a callback from an event type."""
        if event_type in self.listeners:
            if callback in self.listeners[event_type]:
                self.listeners[event_type].remove(callback)

    def publish(self, event_type: str, data: Any = None):
        """Publish an event to all subscribers."""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"EventBus Error processing {event_type}: {e}")
