# src/entities/movement_entity.py
from .basic_entity import BasicEntity
import math
from typing import Tuple, Optional
import pygame
from ..config import TILE_SIZE, PASSABLE_TILES

class MovementEntity(BasicEntity):
    def __init__(self, x: float = 0.0, y: float = 0.0, w: int = 32, h: int = 32,
                 image: Optional[pygame.Surface] = None, shape: str = "rect",
                 game: 'Game' = None, tag: str = "",
                 max_speed: float = 100.0, can_move: bool = True, pass_wall: bool = False, 
                 init_basic: bool = True, **kwargs):
        if init_basic:
            super().__init__(x, y, w, h, image, shape, game, tag, **kwargs)
        self._pass_wall = pass_wall
        self._base_max_speed = max_speed
        self._max_speed = max_speed
        self._speed = max_speed
        self._velocity = (0.0, 0.0)
        self._displacement = (0.0, 0.0)
        self._can_move = can_move

    # Getters (無變動)
    @property
    def max_speed(self) -> float:
        return self._max_speed
    
    @property
    def speed(self) -> float:
        return self._speed
    
    @property
    def velocity(self) -> Tuple[float, float]:
        return self._velocity
    
    @property
    def displacement(self) -> Tuple[float, float]:
        return self._displacement
    
    @property
    def can_move(self) -> bool:
        return self._can_move

    # Setters (無變動)
    @max_speed.setter
    def max_speed(self, value: float) -> None:
        self._max_speed = max(0.0, value)
        self._speed = self._max_speed
    
    @speed.setter
    def speed(self, value: float) -> None:
        self._speed = max(0.0, min(value, self._max_speed))
    
    @velocity.setter
    def velocity(self, value: Tuple[float, float]) -> None:
        self._velocity = value
    
    @displacement.setter
    def displacement(self, value: Tuple[float, float]) -> None:
        self._displacement = value

    def move(self, dx: float, dy: float, dt: float) -> None:
        """Update velocity based on input direction and handle movement."""  # 無變動
        if dx != 0 or dy != 0:
            magnitude = math.sqrt(dx**2 + dy**2)
            if magnitude > 0:
                dx /= magnitude
                dy /= magnitude
            self.velocity = (dx * self.max_speed, dy * self.max_speed)
        else:
            lerp_factor = 0.1
            vx = self.velocity[0] * (1 - lerp_factor)
            vy = self.velocity[1] * (1 - lerp_factor)
            self.velocity = (vx, vy)
            self.displacement = (0.0, 0.0)
            if math.sqrt(vx**2 + vy**2) < self.max_speed * 0.05:
                self.velocity = (0.0, 0.0)

        new_x = self.x + self.velocity[0] * dt
        new_y = self.y + self.velocity[1] * dt
        
        if not self._pass_wall:
            tile_x, tile_y = int(new_x // TILE_SIZE), int(new_y // TILE_SIZE)
            x_valid = 0 <= tile_x < self.dungeon.grid_width
            y_valid = 0 <= tile_y < self.dungeon.grid_height
            if x_valid and y_valid:
                tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile in PASSABLE_TILES:
                    self.set_position(new_x, new_y)
                else:
                    x_allowed = x_valid and self.dungeon.dungeon_tiles[int(self.y // TILE_SIZE)][tile_x] in PASSABLE_TILES
                    y_allowed = y_valid and self.dungeon.dungeon_tiles[tile_y][int(self.x // TILE_SIZE)] in PASSABLE_TILES
                    if x_allowed:
                        self.set_position(new_x, self.y)
                        self.velocity = (self.velocity[0], 0.0)
                    if y_allowed:
                        self.set_position(self.x, new_y)
                        self.velocity = (0.0, self.velocity[1])
                    if not (x_allowed or y_allowed):
                        self.velocity = (0.0, 0.0)
        else:
            self.set_position(new_x, new_y)
        
    def update(self, dt: float, current_time: float) -> None:
        """Update movement entity position based on velocity."""  # 無變動
        if self.can_move:
            self.move(self.displacement[0], self.displacement[1], dt)