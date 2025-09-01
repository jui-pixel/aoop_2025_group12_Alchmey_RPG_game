from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame
from src.entities.character.weapons.weapon import Weapon, Bullet
from src.entities.character.skills.skill import Skill
from src.entities.movable_entity import MovableEntity
from src.config import TILE_SIZE, MAX_WEAPONS_DEFAULT, MAX_SKILLS_DEFAULT, MAX_WEAPON_CHAINS_DEFAULT, MAX_WEAPON_CHAIN_LENGTH_DEFAULT

@dataclass
class Player(MovableEntity):
    weapons: List[Weapon] = None
    current_weapon_idx: int = 0
    skills: List[Tuple[Skill, str]] = None  # List of (skill, key_binding) pairs
    max_weapons: int = MAX_WEAPONS_DEFAULT
    last_fired: float = 0.0
    direction: Tuple[float, float] = (0.0, 0.0)
    max_energy: float = 100.0
    energy: float = 100.0
    energy_regen_rate: float = 20.0

    def __post_init__(self):
        super().__init__(pos=self.pos, game=self.game, size=TILE_SIZE // 2, color=(0, 255, 0))
        if self.weapons is None:
            self.weapons = []
        if self.skills is None:
            self.skills = []
        self.speed = 300.0
        self.health = 100
        self.max_health = 100
        self.base_health = 100
        self.base_defense = 0
        self.energy = self.max_energy
        self.original_energy_regen_rate = 20.0
        
    def __init__(self, pos: Tuple[float, float], game: 'Game', size=TILE_SIZE // 2, color=(0, 255, 0)):
        super().__init__(pos=pos, game=game, size=size, color=color, base_vision_radius=12)
        self.base_speed = 5 * TILE_SIZE
        self.speed = self.base_speed
        self.weapons = []
        self.weapon_chain = [[]]
        self.current_weapon_idx = 0
        self.current_weapon_chain_idx = 0
        self.skills = []
        self.current_skill_idx = 0
        self.max_skills = MAX_SKILLS_DEFAULT
        self.max_weapons = MAX_WEAPONS_DEFAULT
        self.max_weapon_chains = MAX_WEAPON_CHAINS_DEFAULT
        self.max_weapon_chain_length = MAX_WEAPON_CHAIN_LENGTH_DEFAULT
        self.last_fired = 0.0
        self.fire_rate = 0.1
        self.cooldown = 0.0
        self.invulnerable = 1.0
        self.direction = (0.0, 0.0)
        self.max_energy = 100.0
        self.base_defense = 10
        self.eff_defense = self.base_defense
        self.energy = self.max_energy
        self.original_energy_regen_rate = 20.0
        self.energy_regen_rate = 20.0
        self.fog = True

    def update(self, dt: float, current_time: float) -> None:
        super().update(dt, current_time)
        self.energy = min(self.max_energy, self.energy + self.energy_regen_rate * dt)
    
    def fire(self, direction: Tuple[float, float], current_time: float, target_position: Tuple[float, float]) -> Optional['Bullet']:
        weapon = self.weapon_chain[self.current_weapon_chain_idx][self.current_weapon_idx] if self.weapon_chain[self.current_weapon_chain_idx] else None
        if weapon and weapon.can_fire(current_time, self.energy) and self.game and self.dungeon and self.canfire():
            bullet = weapon.fire(self.pos, direction, current_time, self.dungeon, self, target_position)
            if bullet:
                self.last_fired = current_time
                self.energy -= weapon.energy_cost
                # 自動切換到下一個武器
                if len(self.weapon_chain[self.current_weapon_chain_idx]) > 1:
                    self.current_weapon_idx = (self.current_weapon_idx + 1) % len(self.weapon_chain[self.current_weapon_chain_idx])
                    print(f"Switched to weapon: {self.weapon_chain[self.current_weapon_chain_idx][self.current_weapon_idx].name}")
            return bullet
        return None