"""
Tile definitions and Bitmasking utilities for dungeon rendering.
"""
from enum import Enum, auto
from typing import Dict, Set

# Tile Type Constants
TILE_OUTSIDE = "Outside"
TILE_FLOOR = "Room_floor"
TILE_WALL = "Border_wall"
TILE_DOOR = "Door"
TILE_BRIDGE = "Bridge_floor"

# Passable tiles set
PASSABLE_TILES: Set[str] = {
    'Room_floor', 'Bridge_floor', 'Door',
    'Start_room_floor', 'End_room_floor', 'Monster_room_floor',
    'Trap_room_floor', 'Reward_room_floor', 'NPC_room_floor',
    'Lobby_room_floor', 'Boss_room_floor', 'Final_room_floor',
    'Player_spawn', 'Monster_spawn', 'NPC_spawn', 'Boss_spawn',
    'End_room_portal',
}

# Wall types for bitmasking
class WallType(Enum):
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()

def get_wall_bitmask(grid, x: int, y: int) -> int:
    """
    Calculate bitmask based on surrounding tiles for wall autotiling.
    Uses 4-bit mask for cardinal directions.
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    def is_wall(tx, ty):
        if 0 <= tx < width and 0 <= ty < height:
            return grid[ty][tx] not in PASSABLE_TILES
        return True  # Out of bounds = wall
    
    mask = 0
    if is_wall(x, y - 1): mask |= 1  # Top
    if is_wall(x + 1, y): mask |= 2  # Right
    if is_wall(x, y + 1): mask |= 4  # Bottom
    if is_wall(x - 1, y): mask |= 8  # Left
    
    return mask

def get_wall_tile_name(bitmask: int) -> str:
    """
    Convert bitmask to wall tile name for tileset lookup.
    """
    # Basic mapping - can be extended for more complex autotiling
    tile_map = {
        0: 'Border_wall',
        1: 'Border_wall_top',
        2: 'Border_wall_right',
        3: 'Border_wall_top_right_corner',
        4: 'Border_wall_bottom',
        5: 'Border_wall', # Vertical
        6: 'Border_wall_bottom_right_corner',
        8: 'Border_wall_left',
        9: 'Border_wall_top_left_corner',
        10: 'Border_wall', # Horizontal
        12: 'Border_wall_bottom_left_corner',
        # ... more combinations
    }
    return tile_map.get(bitmask, 'Border_wall')
