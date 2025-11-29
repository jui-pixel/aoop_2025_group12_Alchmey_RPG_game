from dataclasses import dataclass
from dataclasses import dataclass

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
from dataclasses import dataclass
from dataclasses import dataclass

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
    resistances: dict = None
    invulnerable: bool = False

@dataclass
class Combat:
    damage: int = 0
    can_attack: bool = True
    atk_element: str = "untyped"
    damage_to_element: dict = None
    max_penetration_count: int = 0
    current_penetration_count: int = 0
    collision_cooldown: float = 0.2
    collision_list: dict = None
    explosion_range: float = 0.0
    explosion_damage: int = 0
    explosion_element: str = "untyped"

@dataclass
class Renderable:
    image: object = None  # pygame.Surface
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
    active_buffs: list = None # List[Buff]
    modifiers: dict = None

@dataclass
class AI:
    behavior_tree: object = None
    current_action: str = "idle"
    action_list: list = None
    actions: dict = None