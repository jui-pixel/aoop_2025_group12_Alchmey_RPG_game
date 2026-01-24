import math
from typing import Tuple

class Vector2:
    """Simple 2D vector class."""
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self) -> 'Vector2':
        mag = self.magnitude()
        if mag > 0:
            return Vector2(self.x / mag, self.y / mag)
        return Vector2(0, 0)
    
    def dot(self, other: 'Vector2') -> float:
        return self.x * other.x + self.y * other.y
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


def world_to_grid(world_x: float, world_y: float, tile_size: int) -> Tuple[int, int]:
    """Convert world coordinates to grid coordinates."""
    return int(world_x // tile_size), int(world_y // tile_size)

def grid_to_world(grid_x: int, grid_y: int, tile_size: int) -> Tuple[float, float]:
    """Convert grid coordinates to world coordinates (center of tile)."""
    return grid_x * tile_size + tile_size / 2, grid_y * tile_size + tile_size / 2

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t

def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
