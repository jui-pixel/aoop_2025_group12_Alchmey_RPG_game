from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable


@dataclass
class Skill:
    name: str
    cooldown: float
    effect: Callable
    last_used: float = 0.0

    def can_use(self, player: 'Player', current_time: float) -> bool:
        if self.cooldown == 0:
            return True
        return (current_time - self.last_used) >= self.cooldown

    def use(self, player: 'Player', current_time: float):
        if self.can_use(player, current_time):
            try:
                self.effect(player)
                if self.cooldown > 0:
                    self.last_used = current_time
            except Exception as e:
                print(f"Skill {self.name} effect failed: {e}")
