import pygame
from typing import Tuple, Optional
from src.config import TILE_SIZE, RED
from src.dungeon.dungeon import Dungeon
from src.weapons.weapon import Bullet

class BasicEnemy(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[float, float], game: 'Game'):
        super().__init__()
        self.pos = list(pos)  # Starting position
        self.game = game
        self.dungeon: Dungeon = game.dungeon
        self.speed = 100.0  # Movement speed in pixels per second
        self.health = 50  # Enemy health
        self.max_health = 50
        self.size = TILE_SIZE // 2  # Enemy size (half a tile)
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(RED)  # Red color for enemy
        self.rect = self.image.get_rect(center=self.pos)
        self.damage = 10  # Damage dealt to player on contact
        self.last_hit_time = 0.0  # Last time enemy dealt damage to player
        self.hit_cooldown = 1.0  # Cooldown between dealing damage (seconds)

    def move_towards_player(self, dt: float) -> None:
        """Move enemy towards the player, avoiding walls."""
        if not self.game.player:
            return

        player_pos = self.game.player.pos
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance == 0:
            return

        # Normalize direction
        dx, dy = dx / distance, dy / distance
        new_x = self.pos[0] + dx * self.speed * dt
        new_y = self.pos[1] + dy * self.speed * dt
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)

        # Check for collision with walls
        if (0 <= tile_x < self.dungeon.grid_width and 0 <= tile_y < self.dungeon.grid_height):
            if self.dungeon.dungeon_tiles[tile_y][tile_x] not in ('Border_wall', 'Outside'):
                self.pos = [new_x, new_y]
                self.rect.center = self.pos
            else:
                # Try moving only in x or y direction to slide along walls
                tile_x = int(self.pos[0] // TILE_SIZE)
                tile_y = int(new_y // TILE_SIZE)
                if (0 <= tile_y < self.dungeon.grid_height and 
                    self.dungeon.dungeon_tiles[tile_y][tile_x] not in ('Border_wall', 'Outside')):
                    self.pos[1] = new_y
                    self.rect.centery = self.pos[1]
                else:
                    tile_x = int(new_x // TILE_SIZE)
                    tile_y = int(self.pos[1] // TILE_SIZE)
                    if (0 <= tile_x < self.dungeon.grid_width and 
                        self.dungeon.dungeon_tiles[tile_y][tile_x] not in ('Border_wall', 'Outside')):
                        self.pos[0] = new_x
                        self.rect.centerx = self.pos[0]

    def take_damage(self, damage: int) -> bool:
        """Apply damage to enemy. Returns True if enemy is killed."""
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True
        return False

    def check_collision_with_player(self, current_time: float) -> None:
        """Check if enemy collides with player and deal damage."""
        if not self.game.player or self.game.player.invulnerable > 0:
            return
        if current_time - self.last_hit_time < self.hit_cooldown:
            return
        if self.rect.colliderect(self.game.player.rect):
            self.game.player.health -= self.damage
            self.last_hit_time = current_time
            if self.game.player.health <= 0:
                print("Player died!")  # Future: Implement game over state

    def update(self, dt: float, current_time: float) -> None:
        """Update enemy state."""
        self.move_towards_player(dt)
        self.check_collision_with_player(current_time)