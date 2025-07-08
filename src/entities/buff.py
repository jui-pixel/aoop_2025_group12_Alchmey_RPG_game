
from typing import Dict, Callable, Optional
class Buff:
    def __init__(self, name: str, duration: float, effects: Dict[str, float], on_apply: Optional[Callable[['MovableEntity'], None]] = None, on_remove: Optional[Callable[['MovableEntity'], None]] = None):
        self.name = name
        self.duration = duration  # Duration in seconds
        self.remaining_time = duration
        self.effects = effects  # e.g., {"speed_multiplier": 1.5, "health_regen_per_second": 5}
        self.on_apply = on_apply  # Optional callback when buff is applied
        self.on_remove = on_remove  # Optional callback when buff is removed
