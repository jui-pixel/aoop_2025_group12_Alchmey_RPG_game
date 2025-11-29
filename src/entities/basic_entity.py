```python
# src/entities/basic_entity.py
import pygame
from typing import Optional, List
from src.ecs.components import Position

class BasicEntity(pygame.sprite.Sprite):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: int = 32, h: int = 32,
                 image: Optional[pygame.Surface] = None, shape: str = "rect",
                 game: 'Game' = None, tag: str = "", **kwargs):
        self.game = game
        self.tag = tag
        self.id = id(self)  # Unique identifier
        self.w = w
        self.h = h
        self.image = image
        self.shape = shape
        
        # ECS Initialization
        self.ecs_entity = None
        # Initialize _x and _y for cases where ECS is not used or not yet initialized
        self._x = x
        self._y = y
        if self.game and hasattr(self.game, 'ecs_world'):
            self.ecs_entity = self.game.ecs_world.create_entity()
            self.game.ecs_world.add_component(self.ecs_entity, Position(x=x, y=y))
        
        # Initialize rect (depends on x/y, which now depend on ECS if available)
        # We use the property setters here
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h) if image is None else image.get_rect(center=(x, y))
        
        self.dungeon = game.dungeon_manager.get_dungeon() if game else None
        super().__init__(**kwargs)  # Pass remaining kwargs to next class in MRO

    @property
    def x(self) -> float:
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            return self.game.ecs_world.component_for_entity(self.ecs_entity, Position).x
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            self.game.ecs_world.component_for_entity(self.ecs_entity, Position).x = value
        self._x = value

    @property
    def y(self) -> float:
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            return self.game.ecs_world.component_for_entity(self.ecs_entity, Position).y
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            self.game.ecs_world.component_for_entity(self.ecs_entity, Position).y = value
        self._y = value

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
        
    def destroy(self):
        """Remove from ECS world."""
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
             self.game.ecs_world.delete_entity(self.ecs_entity)
             self.ecs_entity = None
```