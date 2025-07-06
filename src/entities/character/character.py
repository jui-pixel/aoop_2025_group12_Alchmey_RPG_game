# src/character/character.py
from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame
from src.entities.character.weapons.weapon import Weapon, Bullet
from src.entities.character.skills.skill import Skill
from src.entities.movable_entity import MovableEntity
from src.config import TILE_SIZE, MAX_WEAPONS_DEFAULT

@dataclass
class Player(MovableEntity):
    weapons: List[Weapon] = None
    current_weapon_idx: int = 0
    skill: Optional[Skill] = None
    max_weapons: int = MAX_WEAPONS_DEFAULT
    last_fired: float = 0.0
    invulnerable: float = 0.0
    direction: Tuple[float, float] = (0.0, 0.0)

    def __post_init__(self):
        super().__init__(pos=self.pos, game=self.game, size=TILE_SIZE // 2, color=(0, 255, 0))
        if self.weapons is None:
            self.weapons = []
        self.speed = 300.0
        self.health = 100
        self.max_health = 100
        
    def __init__(self, pos: Tuple[float, float], game: 'Game', size=TILE_SIZE // 2, color=(0, 255, 0)):
        super().__init__(pos=pos, game=game, size=size, color=color)
        self.speed = 300.0
        self.weapons = []
        self.current_weapon_idx = 0
        self.skill = None
        self.max_weapons = MAX_WEAPONS_DEFAULT
        self.last_fired = 0.0
        self.invulnerable = 0.0
        self.direction = (0.0, 0.0)
        
    def fire(self, direction: Tuple[float, float], current_time: float) -> Optional['Bullet']:
        weapon = self.weapons[self.current_weapon_idx] if self.weapons else None
        if weapon and weapon.can_fire(self.last_fired, current_time) and self.game and self.dungeon:
            bullet = weapon.fire(self.pos, direction, current_time, self.dungeon, self)
            if bullet:
                self.last_fired = current_time
            return bullet
        return None