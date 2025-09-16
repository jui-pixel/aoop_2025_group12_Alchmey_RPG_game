from typing import Optional, Dict, Tuple, List
import math
from ..buff.element_buff import ElementBuff, ELEMENTAL_BUFFS, apply_elemental_buff
from ...entities.bullet.bullet import Bullet
from .abstract_skill import Skill


class ShootingSkill(Skill):
    def __init__(self, name: str, element: str, energy_cost: float, element_buff_enable: bool = False,
                 bullet_damage: int = 0, bullet_speed: float = 0, bullet_size: int = 0,
                 bullet_element: str = "untyped", bullet_max_hp_percentage_damage : int = 0,
                 bullet_current_hp_percentage_damage : int = 0,
                 bullet_lose_hp_percentage_damage : int = 0,
                 cause_death: bool = True,
                 max_penetration_count: int = 0, collision_cooldown: float = 0.2,
                 explosion_range: float = 0.0, explosion_damage: int = 0,
                 explosion_max_hp_percentage_damage : int = 0,
                 explosion_current_hp_percentage_damage : int = 0,
                 explosion_lose_hp_percentage_damage : int = 0,
                 explosion_element: str = "untyped",
                 pass_wall: bool = False):
        super().__init__(name, "shooting", element, energy_cost)
        
        self.element_buff_enable = element_buff_enable
        
        self.bullet_damage = bullet_damage
        self.bullet_max_hp_percentage_damage = bullet_max_hp_percentage_damage
        self.bullet_current_hp_percentage_damage = bullet_current_hp_percentage_damage
        self.bullet_lose_hp_percentage_damage = bullet_lose_hp_percentage_damage
        self.cause_death = cause_death
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.bullet_element = bullet_element
        self.bullet_effects = [ELEMENTAL_BUFFS[bullet_element]] if element_buff_enable else []
        
        self.max_penetration_count = max_penetration_count
        
        self.collision_cooldown = collision_cooldown
        
        self.explosion_range = explosion_range
        self.explosion_damage = explosion_damage
        self.explosion_max_hp_percentage_damage = explosion_max_hp_percentage_damage
        self.explosion_current_hp_percentage_damage = explosion_current_hp_percentage_damage
        self.explosion_lose_hp_percentage_damage = explosion_lose_hp_percentage_damage
        self.explosion_element = explosion_element
        self.explosion_buffs = [ELEMENTAL_BUFFS[explosion_element]] if element_buff_enable else []
        
        self.pass_wall = pass_wall

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
            damage=self.damage,
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
        game.entity_manager.player_bullet_group.add(bullet)