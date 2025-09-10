from typing import Optional, Dict, Tuple, List
import pygame
from ..basic_entity import BasicEntity
from ..health_entity import HealthEntity
from ...config import *

class Dummy(HealthEntity):
    """A stationary, invulnerable dummy entity with infinite health and automatic health regeneration."""
    
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 32, 
                 h: int = 32, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "dummy",
                 base_max_hp: int = 999999999,  # Effectively infinite health
                 max_shield: int = 0,
                 dodge_rate: float = 0.0,
                 element: str = "untyped",
                 defense: int = 0,
                 resistances: Optional[Dict[str, float]] = None,
                 invulnerable: bool = True):
        super().__init__(
            x=x, y=y, w=w, h=h, image=image, shape=shape, game=game, tag=tag,
            base_max_hp=base_max_hp, max_shield=max_shield, dodge_rate=dodge_rate,
            element=element, defense=defense, resistances=resistances, invulnerable=invulnerable
        )
        self._regen_rate: float = 1000000.0  # High regeneration rate per second

    def update(self, dt: float, current_time: float) -> None:
        """Update the dummy entity to regenerate health automatically."""
        if not self.invulnerable:
            # Regenerate health rapidly to simulate infinite health
            self.heal(int(self._regen_rate * dt))
        
        # No movement or attack logic, as dummy is stationary and non-attacking
        super().update(dt, current_time)

    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                    max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                    lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """Override take_damage to ensure no death and rapid health recovery."""
        if self.invulnerable:
            return False, 0
        
        # Apply damage but ensure health doesn't drop too low
        killed, damage = super().take_damage(
            factor=factor, element=element, base_damage=base_damage,
            max_hp_percentage_damage=max_hp_percentage_damage,
            current_hp_percentage_damage=current_hp_percentage_damage,
            lose_hp_percentage_damage=lose_hp_percentage_damage,
            cause_death=False  # Prevent death
        )
        
        # Immediately regenerate to simulate infinite health
        self.heal(damage)
        return False, damage  # Dummy cannot be killed