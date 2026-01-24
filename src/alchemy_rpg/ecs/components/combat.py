from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class Health:
    base_max_hp: int = 100
    max_hp: int = 100
    current_hp: int = 100
    max_shield: int = 0
    current_shield: int = 0
    regen_rate: float = 0.0

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
    max_penetration_count: int = 2147483647
    current_penetration_count: int = 0
    collision_cooldown: float = 0.2
    collision_list: Dict[int, float] = field(default_factory=dict)
    explosion_range: float = 0.0
    explosion_damage: int = 0
    explosion_element: str = "untyped"
    max_hp_percentage_damage: int = 0
    current_hp_percentage_damage: int = 0
    lose_hp_percentage_damage: int = 0
    cause_death: bool = True
    buffs: List = field(default_factory=list)
    explosion_max_hp_percentage_damage: int = 0
    explosion_current_hp_percentage_damage: int = 0
    explosion_lose_hp_percentage_damage: int = 0
    explosion_buffs: List = field(default_factory=list)

@dataclass
class BossComponent:
    boss_name: str = "BOSS"
    is_boss: bool = True
