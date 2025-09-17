from typing import Optional, Dict, Tuple, List
import math
from ..buff.element_buff import ElementBuff, ELEMENTAL_BUFFS, apply_elemental_buff
from ...entities.bullet.bullet import Bullet
from .abstract_skill import Skill
from ...config import TILE_SIZE

class ShootingSkill(Skill):
    def __init__(self, name: str, element: str, energy_cost: float = 20.0,
                 damage_level: int = 0, penetration_level: int = 0, elebuff_level: int = 0,
                 explosion_level: int = 0, speed_level: int = 0):
        super().__init__(name, "shooting", element, energy_cost)
        
        # Level-based parameters
        self.damage_level = damage_level
        self.penetration_level = penetration_level
        self.elebuff_level = elebuff_level
        self.explosion_level = explosion_level
        self.speed_level = speed_level
        
        # Calculated values based on levels (moved from skill.py)
        self.bullet_damage = 10 * (1 + 0.1 * damage_level)  # +10% damage per level
        self.bullet_speed = 3 * TILE_SIZE * (1 + 0.1 * speed_level)  # +10% speed per level
        self.bullet_size = 8  # Fixed size, as in original skill.py
        self.bullet_element = element
        self.max_penetration_count = penetration_level  # Direct mapping from penetration_level
        self.explosion_range = explosion_level * 10  # +10 pixels per level (arbitrary scaling)
        self.element_buff_enable = elebuff_level > 0  # Enable elemental buff if elebuff_level > 0
        
        # Default values for other parameters (as in original skill.py)
        self.bullet_max_hp_percentage_damage = 0
        self.bullet_current_hp_percentage_damage = 0
        self.bullet_lose_hp_percentage_damage = 0
        self.explosion_damage = explosion_level * 10  # +10 damage per explosion level
        self.explosion_max_hp_percentage_damage = 0
        self.explosion_current_hp_percentage_damage = 0
        self.explosion_lose_hp_percentage_damage = 0
        self.explosion_element = element
        self.collision_cooldown = 0.2
        self.pass_wall = False
        self.cause_death = True
        
        self.bullet_effects = [ELEMENTAL_BUFFS[element]] if self.element_buff_enable else []
        self.explosion_buffs = [ELEMENTAL_BUFFS[element]] if self.element_buff_enable else []

    def activate(self, player: 'Player', game: 'Game', target_position: Tuple[float, float], current_time: float) -> None:
        if player.energy < self.energy_cost:
            print(f"Not enough energy for {self.name} (required: {self.energy_cost}, available: {player.energy})")
            return

        player.energy -= self.energy_cost
        self.last_used = current_time

        dx = target_position[0] - (player.x + player.w / 2)
        dy = target_position[1] - (player.y + player.h / 2)
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude == 0:
            return
        direction = (dx / magnitude, dy / magnitude)

        damage_to_element = player.damage_to_element
        
        bullet = Bullet(
            x=player.x + player.w / 2,
            y=player.y + player.h / 2,
            w=self.bullet_size,
            h=self.bullet_size,
            image=None,
            shape="rect",
            game=game,
            tag="player_bullet",
            max_speed=self.bullet_speed,
            direction=direction,
            can_move=True,
            can_attack=True,
            buffs=self.bullet_effects,
            damage_to_element=damage_to_element,
            atk_element=self.element,
            damage=self.bullet_damage,
            max_hp_percentage_damage=self.bullet_max_hp_percentage_damage,
            current_hp_percentage_damage=self.bullet_current_hp_percentage_damage,
            lose_hp_percentage_damage=self.bullet_lose_hp_percentage_damage,
            max_penetration_count=self.max_penetration_count,
            collision_cooldown=self.collision_cooldown,
            explosion_range=self.explosion_range,
            explosion_damage=self.explosion_damage,
            explosion_max_hp_percentage_damage=self.explosion_max_hp_percentage_damage,
            explosion_current_hp_percentage_damage=self.explosion_current_hp_percentage_damage,
            explosion_lose_hp_percentage_damage=self.explosion_lose_hp_percentage_damage,
            explosion_element=self.explosion_element,
            explosion_buffs=self.explosion_buffs,
            pass_wall=self.pass_wall
        )
        game.entity_manager.bullet_group.add(bullet)