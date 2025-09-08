from typing import Optional, Dict, Tuple
from ..buff.element_buff import ElementBuff, apply_elemental_buff
from ...entities.bullet.bullet import Bullet
import math

class Skill:
    def __init__(self, name: str, type: str, element: str, energy_cost: float,
                 damage: int = 0, bullet_speed: float = 0, bullet_size: int = 0,
                 buff: str = None, buff_duration: float = 0, effect: Dict = None):
        self.name = name
        self.type = type  # "shooting", "defense", or "movement"
        self.element = element
        self.energy_cost = energy_cost
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.buff = buff
        self.buff_duration = buff_duration
        self.effect = effect or {}
        self.last_used = 0.0

    def activate(self, player: 'Player', game: 'Game', target_position: Tuple[float, float], current_time: float) -> None:
        if player.energy < self.energy_cost:
            print(f"Not enough energy for {self.name} (required: {self.energy_cost}, available: {player.energy})")
            return

        player.energy -= self.energy_cost

        if self.type == "shooting":
            # Normalize direction
            dx = target_position[0] - player.x
            dy = target_position[1] - player.y
            magnitude = math.sqrt(dx**2 + dy**2)
            if magnitude == 0:
                return
            direction = (dx / magnitude, dy / magnitude)

            # Create bullet with effect
            bullet = Bullet(
                x=player.x + player.w / 2,
                y=player.y + player.h / 2,
                w=self.bullet_size,
                h=self.bullet_size,
                image=None,
                shape="rect",
                game=game,
                tag="player_bullet",
                base_max_hp=self.damage,
                max_speed=self.bullet_speed,
                element=self.element,
                direction=direction,
                effect=self.effect
            )
            game.player_bullet_group.add(bullet)

        elif self.type in ("defense", "movement"):
            # Apply buff to player
            buff = ElementBuff(
                name=self.buff,
                duration=self.buff_duration,
                element=self.element,
                multipliers=self.effect.get("multipliers", {}),
                effect_per_second=None,
                on_apply=None,
                on_remove=None
            )
            player.add_buff(buff)