# src/entities/basic_entity.py
import pygame
from typing import Optional, List

class BasicEntity(pygame.sprite.Sprite):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: int = 32, h: int = 32,
                 image: Optional[pygame.Surface] = None, shape: str = "rect",
                 game: 'Game' = None, tag: str = "", **kwargs):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = image
        self.shape = shape
        self.game = game
        self.tag = tag
        self.id = id(self)  # Unique identifier
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h) if image is None else image.get_rect(center=(x, y))
        self.dungeon = game.dungeon_manager.get_dungeon() if game else None
        super().__init__(**kwargs)  # Pass remaining kwargs to next class in MRO

    def set_position(self, x: float, y: float) -> None:
        """Set the entity's position and update rect."""
        self.x = x
        self.y = y
        if self.image:
            self.rect.center = (x, y)
        else:
            self.rect.topleft = (x - self.w // 2, y - self.h // 2)

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw the entity on the screen with camera offset."""
        screen_x = self.x - camera_offset[0] - self.w // 2
        screen_y = self.y - camera_offset[1] - self.h // 2
        if self.image:
            screen.blit(self.image, (screen_x, screen_y))
            # 除錯：添加邊框
            pygame.draw.rect(screen, (255, 255, 0), (screen_x, screen_y, self.w, self.h), 2)  # 黃色邊框
        else:
            draw_rect = pygame.Rect(screen_x, screen_y, self.w, self.h)
            pygame.draw.rect(screen, (255, 0, 0), draw_rect)
            pygame.draw.rect(screen, (255, 255, 0), draw_rect, 2)  # 邊框

    def update(self, dt: float, current_time: float) -> None:
        """Base update method, to be overridden by subclasses."""
        pass