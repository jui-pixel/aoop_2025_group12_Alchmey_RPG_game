from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class Player:
    pass

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
class Health:
    max_hp: int = 100
    current_hp: int = 100
    max_shield: int = 0
    current_shield: int = 0

@dataclass
class Defense:
    defense: int = 0
    dodge_rate: float = 0.0
    element: str = "untyped"
    resistances: Optional[Dict[str, float]] = None
    invulnerable: bool = False

@dataclass
class Combat:
    damage: int = 0
    can_attack: bool = True
    atk_element: str = "untyped"
    damage_to_element: Optional[Dict[str, float]] = None
    max_penetration_count: int = 0
    current_penetration_count: int = 0
    collision_cooldown: float = 0.2
    collision_list: Dict[int, float] = field(default_factory=dict)
    explosion_range: float = 0.0
    explosion_damage: int = 0
    explosion_element: str = "untyped"
    # Percentage damage
    max_hp_percentage_damage: int = 0
    current_hp_percentage_damage: int = 0
    lose_hp_percentage_damage: int = 0
    cause_death: bool = True
    # Buffs to apply on hit
    buffs: List = field(default_factory=list)  # List[Buff]
    # Explosion percentage damage
    explosion_max_hp_percentage_damage: int = 0
    explosion_current_hp_percentage_damage: int = 0
    explosion_lose_hp_percentage_damage: int = 0
    explosion_buffs: List = field(default_factory=list)  # List[Buff]

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
class Buffs:
    active_buffs: List = field(default_factory=list)  # List[Buff]
    modifiers: Dict[str, float] = field(default_factory=dict)

@dataclass
class Collider:
    w: int = 32
    h: int = 32
    pass_wall: bool = False
    collision_group: str = "default"
    collision_mask: Optional[List[str]] = None

@dataclass
class AI:
    behavior_tree: Optional[object] = None
    current_action: str = "idle"
    action_list: List[str] = field(default_factory=list)
    actions: Dict[str, object] = field(default_factory=dict)