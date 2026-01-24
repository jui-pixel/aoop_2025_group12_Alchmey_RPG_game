from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .room import Room
from .bridge import Bridge

@dataclass
class DungeonContext:
    """
    黑板模式 - 存儲地牢生成過程中的共享數據。
    """
    # Grid dimensions
    grid_width: int = 100
    grid_height: int = 80
    tile_size: int = 32
    
    # Generation results
    rooms: List[Room] = field(default_factory=list)
    bridges: List[Bridge] = field(default_factory=list)
    grid: List[List[str]] = field(default_factory=list)
    
    # Metadata
    dungeon_id: int = 0
    seed: Optional[int] = None
    
    # BSP Tree (optional, depends on algorithm)
    bsp_root: Any = None
    
    # Key positions
    spawn_points: Dict[str, tuple] = field(default_factory=dict)
    
    def reset(self):
        self.rooms = []
        self.bridges = []
        self.grid = [['Outside' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.bsp_root = None
        self.spawn_points = {}
