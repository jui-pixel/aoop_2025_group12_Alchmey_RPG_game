# src/entities/player/player.py
from typing import List, Tuple, Optional, Dict
from ..attack_entity import AttackEntity
from ..buffable_entity import BuffableEntity
from ..health_entity import HealthEntity
from ..movement_entity import MovementEntity
from ..skill.abstract_skill import Skill
from ...config import TILE_SIZE, MAX_SKILLS_DEFAULT
import pygame
import math
from ..basic_entity import BasicEntity  # Import BasicEntity explicitly

class Player(AttackEntity, BuffableEntity, HealthEntity, MovementEntity):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: int = TILE_SIZE // 2, h: int = TILE_SIZE // 2, 
                 image: Optional[pygame.Surface] = None, shape: str = "rect", game: 'Game' = None, tag: str = "",
                 base_max_hp: int = 100, max_shield: int = 0, dodge_rate: float = 0.0, max_speed: float = 3 * TILE_SIZE,
                 element: str = "untyped", defense: int = 10, resistances: Optional[Dict[str, float]] = None, 
                 damage_to_element: Optional[Dict[str, float]] = None, can_move: bool = True, can_attack: bool = True, 
                 invulnerable: bool = False, pass_wall: bool = False, vision_radius: int = 10):
        
        # Initialize BasicEntity first to set core attributes
        BasicEntity.__init__(self, x, y, w, h, image, shape, game, tag)
        
        # Initialize mixins without basic init
        MovementEntity.__init__(self, x, y, w, h, image, shape, game, tag, max_speed, can_move, pass_wall=pass_wall, init_basic=False)
        
        HealthEntity.__init__(self, x, y, w, h, image, shape, game, tag, base_max_hp, max_shield, dodge_rate, element, defense, resistances, invulnerable, init_basic=False)
        
        AttackEntity.__init__(self, x, y, w, h, image, shape, game, tag, can_attack, damage_to_element, 
                             atk_element=element, damage=0, max_penetration_count=0, collision_cooldown=0.2, 
                             explosion_range=0.0, explosion_damage=0, init_basic=False)
        
        BuffableEntity.__init__(self, x, y, w, h, image, shape, game, tag, init_basic=False)
        
        # Player-specific attributes
        self.skill_chain = [[] for _ in range(9)]  # List[List[Skill]] for 9 skill chains
        self.current_skill_chain_idx = 0
        self.current_skill_idx = 0
        self.max_skills = MAX_SKILLS_DEFAULT
        self.max_skill_chains = 9
        self.max_skill_chain_length = 8  # Updated to 8 as per menu description
        self.base_max_energy = 100.0
        self.max_energy = self.base_max_energy
        self.energy = self.max_energy
        self.energy_regen_rate = 20.0
        self.original_energy_regen_rate = 20.0
        self.fog = True
        self.vision_radius = vision_radius  # In tiles
        self.mana = 0 # 貨幣單位

    def update(self, dt: float, current_time: float) -> None:
        # Call parent classes' update methods in order
        MovementEntity.update(self, dt, current_time)
        HealthEntity.update(self, dt, current_time)
        AttackEntity.update(self, dt, current_time)
        BuffableEntity.update(self, dt, current_time)
        self.regenerate_energy(dt)

    def regenerate_energy(self, dt: float) -> None:
        """Regenerate energy over time."""
        if self.energy < self.max_energy:
            self.energy += self.energy_regen_rate * dt
            if self.energy > self.max_energy:
                self.energy = self.max_energy
    
    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        # Draw the player as a white rectangle
        pygame.draw.rect(screen, (255, 255, 255), 
                         (self.x - camera_offset[0], self.y - camera_offset[1], self.w, self.h))

    def add_skill_to_chain(self, skill: Skill, chain_idx: int = 0) -> bool:
        """Add a skill to the specified skill chain if space is available."""
        if chain_idx >= self.max_skill_chains:
            print(f"Invalid chain index: {chain_idx}. Maximum is {self.max_skill_chains - 1}.")
            return False
        if len(self.skill_chain) <= chain_idx:
            self.skill_chain.extend([[] for _ in range(chain_idx - len(self.skill_chain) + 1)])
        if len(self.skill_chain[chain_idx]) < self.max_skill_chain_length:
            self.skill_chain[chain_idx].append(skill)
            return True
        print(f"Skill chain {chain_idx} is full (max length: {self.max_skill_chain_length}).")
        return False

    def switch_skill_chain(self, chain_idx: int) -> None:
        """Switch to the specified skill chain."""
        if 0 <= chain_idx < len(self.skill_chain):
            self.current_skill_chain_idx = chain_idx
            self.current_skill_idx = 0
            print(f"Switched to skill chain {chain_idx + 1}/{len(self.skill_chain)}")
        else:
            print(f"Invalid chain index: {chain_idx}. Available chains: {len(self.skill_chain)}")

    def switch_skill(self, index: int) -> None:
        """Switch to the specified skill in the current skill chain."""
        if 0 <= self.current_skill_chain_idx < len(self.skill_chain):
            if 0 <= index < len(self.skill_chain[self.current_skill_chain_idx]):
                self.current_skill_idx = index
                print(f"Switched to skill: {self.skill_chain[self.current_skill_chain_idx][self.current_skill_idx].name}")
            else:
                print(f"Invalid skill index: {index}. Available skills: {len(self.skill_chain[self.current_skill_chain_idx])}")

    def activate_skill(self, direction: Tuple[float, float], current_time: float, target_position: Tuple[float, float]) -> None:
        """Activate the current skill in the active skill chain."""
        if not self.game or not self.skill_chain[self.current_skill_chain_idx]:
            print("No skills available in current chain or game not initialized.")
            return

        skill = self.skill_chain[self.current_skill_chain_idx][self.current_skill_idx]
        if self.energy < skill.energy_cost:
            print(f"Not enough energy for {skill.name} (required: {skill.energy_cost}, available: {self.energy})")
            return

        skill.activate(self, self.game, target_position, current_time)
        self.energy -= skill.energy_cost
        assert self.energy >= 0, "Energy should not be negative after skill activation"
        # Auto-switch to next skill in chain
        if len(self.skill_chain[self.current_skill_chain_idx]) > 1:
            self.current_skill_idx = (self.current_skill_idx + 1) % len(self.skill_chain[self.current_skill_chain_idx])
            print(f"Switched to skill: {self.skill_chain[self.current_skill_chain_idx][self.current_skill_idx].name}")

    def canfire(self) -> bool:
        """Check if the player can activate a skill."""
        return self.can_attack