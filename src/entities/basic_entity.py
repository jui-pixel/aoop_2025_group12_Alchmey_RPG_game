"""
Basic Entity Implementation
This module provides a basic implementation of the EntityInterface for simple entities.
"""
from abc import ABC, abstractmethod
from turtle import position
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from src.game import Game

class BasicEntity(pygame.sprite.Sprite):
    """
    Main entity interface that defines the core structure for all game entities.
    This is the central hub that coordinates all component interfaces.
    """
    
    def __init__(self, x: float, y: float, w: int, h: int, 
                 image: pygame.Surface, shape: str, game: 'Game', tag: str = ""):
        self.id = id(self)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = image
        self.rect = self.image.get_rect(center=self.pos)
        self.shape = shape
        self.game = game
        self.dungeon = game.dungeon_manager.get_dungeon()
        self.tag = tag

    
    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw the entity on the screen."""
        if not self.image:
            return
        
        # Calculate screen position with camera offset
        screen_x = self.x + camera_offset[0] - self.w // 2
        screen_y = self.y + camera_offset[1] - self.h // 2
        
        # Draw the entity
        screen.blit(self.image, (screen_x, screen_y))
        
    
    def update(self, dt: float, current_time: float) -> None:
        """Update the entity."""
        pass
    
    def set_position(self, new_x, new_y):
        self.x, self.y = (new_x, new_y)
        
