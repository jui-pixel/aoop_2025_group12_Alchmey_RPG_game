# Base class for movement mechanics
from .basic_entity import BasicEntity
import math
from typing import *
import pygame

class MovementEntity(BasicEntity):
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 32, 
                 h: int = 32, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "",
                 max_speed: float = 100.0,
                 can_move: bool = True):
        super().__init__(x, y, w, h, image, shape, game, tag)
        
        # Movement
        self._base_max_speed: float = max_speed
        self._max_speed: float = max_speed
        self._speed: float = max_speed
        self._velocity: Tuple[float, float] = (0.0, 0.0)
        self._displacement: Tuple[float, float] = (0.0, 0.0)
        
        self._can_move: bool = can_move

    # Getters
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

    # Setters
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
    
    @can_move.setter
    def can_move(self, value: bool) -> None:
        self._can_move = value

    def move(self, dx: float, dy: float, dt: float) -> None:
        if not self.can_move:
            self.velocity = (0.0, 0.0)
            self.displacement = (0.0, 0.0)
            return

        # Calculate input magnitude
        length = math.sqrt(dx**2 + dy**2)
        
        if length > 0:
            # Full speed in input direction
            dx, dy = dx / length, dy / length
            self.displacement = (dx, dy)
            self.velocity = (dx * self.max_speed, dy * self.max_speed)
        else:
            # Lerp velocity towards zero
            lerp_factor = 0.1
            vx = self.velocity[0] * (1 - lerp_factor)
            vy = self.velocity[1] * (1 - lerp_factor)
            self.velocity = (vx, vy)
            self.displacement = (0.0, 0.0)
            
            # Stop if velocity is very low
            if math.sqrt(vx**2 + vy**2) < self.max_speed * 0.05:
                self.velocity = (0.0, 0.0)

        # Update position
        new_x = self.x + self.velocity[0] * dt
        new_y = self.y + self.velocity[1] * dt
        
        if not self.pass_wall:
            tile_x, tile_y = int(new_x // TILE_SIZE), int(new_y // TILE_SIZE)
            
            # Check if new position is valid
            x_valid = 0 <= tile_x < self.dungeon.grid_width
            y_valid = 0 <= tile_y < self.dungeon.grid_height
            
            if x_valid and y_valid:
                tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile in PASSABLE_TILES:
                    self.set_position(new_x, new_y)
                else:
                    # Try sliding along X or Y axis
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