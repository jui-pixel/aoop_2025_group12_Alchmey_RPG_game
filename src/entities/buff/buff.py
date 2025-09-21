# src/entities/buff/buff.py
from typing import Dict, Callable, Optional
class Buff:
    def __init__(self, name: str, duration: float, element: str, multipliers: Dict[str, float],
                 effect_per_second: Optional[Callable["EntityInterface", None]] = None,
                 on_apply: Optional[Callable["EntityInterface", None]] = None,
                 on_remove: Optional[Callable["EntityInterface", None]] = None):
        self.name = name
        self.duration = duration  # Duration in seconds
        self.element = element
        self.effect_time = 0.0
        self.last_effect_time = 0.0
        self.multipliers = multipliers  # e.g., {"speed_multiplier": 1.5, "health_regen_per_second": 5}
        self.effect_per_second = effect_per_second # like damage per second
        self.on_apply = on_apply  # Optional callback when buff is applied
        self.on_remove = on_remove  # Optional callback when buff is removed
    
    def deepcopy(self) -> 'Buff':
        """Create a deep copy of the buff."""
        return Buff(
            name=self.name,
            duration=self.duration,
            element=self.element,
            multipliers=self.multipliers.copy(),
            effect_per_second=self.effect_per_second,
            on_apply=self.on_apply,
            on_remove=self.on_remove
        )
