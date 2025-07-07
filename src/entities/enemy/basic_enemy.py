# src/enemy/basic_enemy.py
import pygame
import math
from typing import Tuple, Optional
from src.entities.movable_entity import MovableEntity
from src.config import TILE_SIZE, RED
from src.entities.character.weapons.weapon import Bullet

class BasicEnemy(MovableEntity):
    def __init__(self, pos: Tuple[float, float], game: 'Game'):
        super().__init__(pos=pos, game=game, size=TILE_SIZE // 2, color=RED)
        self.speed = 100.0
        self.health = 50
        self.max_health = 50
        self.damage = 10
        self.last_hit_time = 0.0
        self.hit_cooldown = 1.0
        # Shooting attributes
        self.fire_rate = 1.5
        self.last_fired = 0.0
        self.bullet_speed = 400.0
        self.bullet_damage = 5
        self.bullet_size = 5

    def move_towards_player(self, dt: float) -> None:
        """Move enemy towards the player."""
        if not self.game.player:
            return

        player_pos = self.game.player.pos
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance == 0:
            return

        # Use inherited move method
        self.move(dx, dy, dt)

    def check_collision_with_player(self, current_time: float) -> None:
        """Check if enemy collides with player and deal damage."""
        if not self.game.player or self.game.player.invulnerable > 0:
            return
        if current_time - self.last_hit_time < self.hit_cooldown:
            return
        if self.rect.colliderect(self.game.player.rect):
            self.game.player.take_damage(self.damage)
            self.last_hit_time = current_time
            if self.game.player.health <= 0:
                print("Player died!")  # Future: Implement game over state

    def attack_player(self, current_time: float) -> None:
        """Attack player by shooting bullets if in range and cooldown allows."""
        if not self.game.player:
            return
        if current_time - self.last_fired < self.fire_rate:
            return
        player_pos = self.game.player.pos
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 500:
            return
        if distance == 0:
            return
        direction = (dx / distance, dy / distance)
        bullet = Bullet(
            pos=self.pos,
            direction=direction,
            speed=self.bullet_speed,
            damage=self.bullet_damage,
            dungeon=self.dungeon,
            shooter=self,
            fire_time=current_time,
        )
        bullet.image = pygame.Surface((self.bullet_size, self.bullet_size))
        bullet.image.fill((255, 0, 0))
        bullet.rect = bullet.image.get_rect(center=self.pos)
        self.game.enemy_bullet_group.add(bullet)
        self.last_fired = current_time

    def update(self, dt: float, current_time: float) -> None:
        """Update enemy state."""
        self.move_towards_player(dt)
        self.check_collision_with_player(current_time)
        self.attack_player(current_time)