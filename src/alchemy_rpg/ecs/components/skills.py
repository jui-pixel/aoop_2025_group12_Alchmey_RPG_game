from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    SkillType = object
else:
    SkillType = object

@dataclass
class Buffs:
    active_buffs: List = field(default_factory=list)
    modifiers: Dict[str, float] = field(default_factory=dict)

@dataclass
class PlayerComponent:
    max_skill_chains: int = 9
    max_skill_chain_length: int = 8
    skill_chain: List[List[List[SkillType]]] = field(default_factory=lambda: [[] for _ in range(9)])
    current_skill_chain_idx: int = 0
    current_skill_idx: int = 0
    
    base_max_energy: float = 100.0
    max_energy: float = 100.0
    energy: float = 100.0
    
    base_energy_regen_rate: float = 20.0
    energy_regen_rate: float = 20.0
    original_energy_regen_rate: float = 20.0
    
    current_shield: int = 0
    max_shield: int = 0
    
    fog: bool = True
    vision_radius: int = 10
    mana: int = 0

@dataclass
class AI:
    behavior_tree: Optional[object] = None
    current_action: str = "idle"
    action_list: List[str] = field(default_factory=list)
    actions: Dict[str, object] = field(default_factory=dict)
    vision_radius: int = 5
    half_hp_triggered: bool = False
