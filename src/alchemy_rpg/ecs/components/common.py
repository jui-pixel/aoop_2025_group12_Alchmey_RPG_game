from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Dict

@dataclass
class Position:
    x: float
    y: float

@dataclass
class Velocity:
    x: float = 0.0
    y: float = 0.0
    speed: float = 100.0

@dataclass
class Tag:
    tag: str = "untagged"

@dataclass
class Renderable:
    image: Optional[object] = None  # pygame.Surface
    shape: str = "rect"
    w: int = 32
    h: int = 32
    color: tuple = (255, 255, 255)
    layer: int = 0
    visible: bool = True

@dataclass
class Input:
    dx: float = 0.0
    dy: float = 0.0
    attack: bool = False
    special: bool = False
    target_x: float = 0.0
    target_y: float = 0.0

@dataclass
class TimerComponent:
    """
    通用計時器組件。
    """
    duration: float = 0.0      # 計時器總時間
    elapsed_time: float = 0.0  # 已經過的時間
    on_expire: Optional[object] = None  # Callable[[], None]

@dataclass
class ProjectileState:
    """
    通用拋射物 (Projectile) 的運行狀態組件。
    """
    direction: Tuple[float, float] = (0.0, 0.0) 
    max_speed: float = 300.0  
    can_move: bool = True
    max_lifetime: float = 5.0
    current_lifetime: float = 5.0 # Will be reset in init but dataclass needs default
    explode_on_collision: bool = True
    collision_tracking: Dict[int, float] = field(default_factory=dict)

    def __post_init__(self):
        self.current_lifetime = self.max_lifetime

@dataclass
class ExpansionLifecycle:
    hide_time: float = 0.0
    wait_time: float = 0.0
    is_hidden: bool = field(init=False)
    expanded: bool = False
    explosion_animation_done: bool = False
    
    def __post_init__(self):
        self.is_hidden = self.hide_time > 0

@dataclass
class ExpansionRenderData:
    outer_radius: float = 32.0 
    expansion_duration: float = 1.0
    initial_inner_radius: float = field(init=False)
    current_inner_radius: float = field(init=False)
    expansion_time: float = 0.0
    explosion_animation_time: float = 0.0
    animation_frames: List[object] = field(default_factory=list)

    def __post_init__(self):
        self.initial_inner_radius = self.outer_radius * 0.1
        self.current_inner_radius = self.initial_inner_radius
