import pygame
from typing import Optional, List, Dict
from src.entities.player.player import Player
from src.entities.enemy.enemy1 import enemy1
# from src.entities.npc.crucible import NPC
from src.entities.damage_text import DamageText
from src.config import TILE_SIZE

class EntityManager:
    def __init__(self, game: 'Game'):
        self.game = game
        self.player = None
        self.player_bullet_group = pygame.sprite.Group()
        self.enemy_bullet_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.npc_group = pygame.sprite.Group()
        self.damage_text_group = pygame.sprite.Group()
        self.reward_group = pygame.sprite.Group()
        self.trap_group = pygame.sprite.Group()
        self.environment_group = pygame.sprite.Group()

    def initialize_player(self, x: float, y: float) -> None:
        """Initialize the player at the specified position."""
        self.player = Player(
            x=x, y=y, game=self.game, base_max_hp=100, max_speed=20 * TILE_SIZE, 
            element="untyped", defense=10, resistances=None, damage_to_element=None,
            can_move=True, can_attack=True, invulnerable=False
        )

    def update(self, dt: float, current_time: float) -> None:
        """Update all entities."""
        if self.player:
            self.player.update(dt, current_time)
        self.player_bullet_group.update(dt, current_time)
        self.enemy_bullet_group.update(dt, current_time)
        self.enemy_group.update(dt, current_time)
        self.npc_group.update(dt, current_time)
        self.damage_text_group.update(dt, current_time)
        self.reward_group.update(dt, current_time)
        self.trap_group.update(dt, current_time)
        self.environment_group.update(dt, current_time)

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw all entities."""
        if self.player:
            self.player.draw(screen, camera_offset)
        self.player_bullet_group.draw(screen)
        self.enemy_bullet_group.draw(screen)
        self.enemy_group.draw(screen)
        self.npc_group.draw(screen)
        self.damage_text_group.draw(screen)
        self.reward_group.draw(screen)
        self.trap_group.draw(screen)
        self.environment_group.draw(screen)