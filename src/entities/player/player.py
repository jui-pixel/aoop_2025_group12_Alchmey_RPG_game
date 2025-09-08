from typing import *
from combat_entity import CombatEntity
import pygame


class Player(CombatEntity):
    def __init__(self, x: float = 0, y: float = 0, w: int = 32, h: int = 32, 
                 image: Optional[pygame.Surface] = None, shape: str = "rect", 
                 game: 'Game' = None, tag: str = "", base_max_hp: int = 100, 
                 max_shield: int = 0, dodge_rate: float = 0, max_speed: float = 100, 
                 element: str = "untyped", resistances: Optional[Dict[str, float]] = None, 
                 damage_to_element: Optional[Dict[str, float]] = None, can_move: bool = True, 
                 can_attack: bool = True, invulnerable: bool = False):
        super().__init__(x, y, w, h, image, shape, game, tag, base_max_hp, max_shield, 
                         dodge_rate, max_speed, element, resistances, damage_to_element,
                         can_move, can_attack, invulnerable)
        self.base_max_energy = 100.0
        self.max_energy = self.base_max_energy
        self.energy = self.max_energy
        self.base_energy_regen_rate = 20.0
        self.energy_regen_rate = 20.0
        
    def update(self, dt: float, current_time: float) -> None:
        super().update(dt, current_time)
        self.energy = min(self.max_energy, self.energy + self.energy_regen_rate * dt)
        
    def fire(self, direction: Tuple[float, float], current_time: float, target_position: Tuple[float, float]) -> None:
        
        return None
        