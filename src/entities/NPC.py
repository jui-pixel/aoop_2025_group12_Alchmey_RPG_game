from typing import Tuple
from src.config import *
import pygame
import math


class NPC(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[float, float], game: 'Game', name: str = "NPC"):
        super().__init__()
        self.name = name
        self.game = game
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((0, 255, 255))  # Cyan color for NPC
        self.rect = self.image.get_rect(center=pos)
        self.pos = list(pos)
        self.interaction_radius = 2 * TILE_SIZE  # Interaction range

    def can_interact(self, player_pos: Tuple[float, float]) -> bool:
        """Check if player is close enough to interact."""
        distance = math.sqrt((self.pos[0] - player_pos[0]) ** 2 + (self.pos[1] - player_pos[1]) ** 2)
        return distance <= self.interaction_radius

    def draw(self, screen, camera_offset):
        screen.blit(self.image, (self.rect.x + camera_offset[0], self.rect.y + camera_offset[1]))