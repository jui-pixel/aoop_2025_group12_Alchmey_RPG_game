from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable

# Use simple object or forward ref for type hinting if needed, but keeping it simple for now
@dataclass
class Collider:
    w: int = 32
    h: int = 32
    pass_wall: bool = False
    destroy_on_collision: bool = False
    collision_group: str = "default"
    collision_mask: Optional[List[str]] = None

@dataclass
class NPCInteractComponent:
    tag = "npc"
    interaction_range: float = 64.0
    alchemy_options: List[Dict] = field(default_factory=list)
    is_interacting: bool = False
    show_interact_prompt: bool = False
    start_interaction: Optional[Callable[[], None]] = None

@dataclass
class DungeonPortalComponent:
    available_dungeons: List[Dict] = field(default_factory=list)
    portal_effect_active: bool = False

@dataclass
class TreasureStateComponent:
    is_looted: bool = False
