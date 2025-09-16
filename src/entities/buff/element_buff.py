from typing import Dict, List, Optional, Callable
from .buff import Buff
# from ..buffable_entity import BuffableEntity
from ...utils.elements import WEAKTABLE
# Elemental affinities based on the game's interaction table (derived from combat_entity cycle and special affinities)


# Base multipliers for elemental interactions (1.5x damage to weak element, 0.5x to resistant)
AFFINITY_MULTIPLIER_WEAK = 1.5
AFFINITY_MULTIPLIER_RESIST = 0.5
NEUTRAL_MULTIPLIER = 1.0

class ElementBuff(Buff):
    """
    Specialized Buff class for elemental effects.
    Extends Buff to include elemental-specific properties like affinity interactions and merge rules.
    """
    
    def __init__(self, name: str, duration: float, element: str, multipliers: Dict[str, float],
                 effect_per_second: Optional[Callable[["BuffableEntity"], None]] = None,
                 on_apply: Optional[Callable[["BuffableEntity"], None]] = None,
                 on_remove: Optional[Callable[["BuffableEntity"], None]] = None,
                 strength: float = 1.0,  # Buff strength modifier for elemental effects
                 ):
        super().__init__(name, duration, element, multipliers, effect_per_second, on_apply, on_remove)
        self.strength = strength  # Amplifies effect based on elemental interaction
    
    def deepcopy(self) -> 'ElementBuff':
        """Create a deep copy of the elemental buff."""
        return ElementBuff(
            name=self.name,
            duration=self.duration,
            element=self.element,
            multipliers=self.multipliers.copy(),
            effect_per_second=self.effect_per_second,
            on_apply=self.on_apply,
            on_remove=self.on_remove,
            strength=self.strength,
        )
    
    def get_affinity_multiplier(self, target_element: str) -> float:
        """
        Calculate affinity multiplier based on elemental interaction table.
        Returns 1.5 for weak (beats), 0.5 for strong (resists), 1.0 otherwise.
        """
        if self.element == 'untyped' or target_element == 'untyped':
            return NEUTRAL_MULTIPLIER
             
        # Cycle-based interactions
        if (self.element, target_element) in WEAKTABLE:
            return AFFINITY_MULTIPLIER_WEAK
        if (target_element, self.element) in WEAKTABLE:
            return AFFINITY_MULTIPLIER_RESIST
        
        return NEUTRAL_MULTIPLIER


# take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
#                    max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
#                    lose_hp_percentage_damage: int = 0, cause_death: bool = True)

# Predefined Elemental Buffs based on interaction table
ELEMENTAL_BUFFS = {
    'fire': ElementBuff(
        name='Burn',
        duration=3.0,
        element='fire',
        multipliers={},
        effect_per_second=lambda e: e.take_damage(current_hp_percentage_damage=5, element='fire', cause_death = False) if hasattr(e, 'take_damage') else None,
        on_apply=None,
        on_remove=None,
    ),
    'water': ElementBuff(
        name='Humid',
        duration=3.0,
        element='water',
        multipliers={'electric_resistance_multiplier': -0.2, 'wood_resistance_multiplier': -0.2},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'earth': ElementBuff(
        name='Dist',
        duration=3.0,
        element='earth',
        multipliers={'speed_multiplier': 0.9, 'vision_radius_multiplier': 0.9},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'wood': ElementBuff(
        name='Entangled',
        duration=3.0,
        element='wood',
        multipliers={'speed_multiplier': 0.0,},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'metal': ElementBuff(
        name='Tear',
        duration=3.0,
        element='metal',
        multipliers={'defense_multiplier': 0.8,},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'ice': ElementBuff(
        name='Cold',
        duration=3.0,
        element='ice',
        multipliers={'speed_multiplier': 0.6,},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'electric': ElementBuff(
        name='Paralysis',
        duration=3.0,
        element='electric',
        multipliers={'speed_multiplier': 0.0, 'can_attack_multiplier': 0.0},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'wind': ElementBuff(
        name='Disorder',
        duration=3.0,
        element='wind',
        multipliers={},
        effect_per_second=lambda e: [setattr(b, 'duration', b.duration + 0.5) for b in e.buffs] if hasattr(e, 'buffs') else None,
        on_apply=None,
        on_remove=None,
    ),
    'light': ElementBuff(
        name='Blind',
        duration=3.0,
        element='light',
        multipliers={'vision_radius_multiplier': 0.7},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'dark': ElementBuff(
        name='Erosion',
        duration=3.0,
        element='dark',
        multipliers={},
        effect_per_second=lambda e: e.take_damage(max_hp_percentage_damage=5, element='dark') if hasattr(e, 'take_damage') else None,
        on_apply=None,
        on_remove=None,
    ),
    'Mud': ElementBuff(
        name='Mud',
        duration=3.0,
        element='earth',
        multipliers={'speed_multiplier': 0.1,},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'Freeze': ElementBuff(
        name='Freeze',
        duration=3.0,
        element='ice',
        multipliers={'speed_multiplier': 0.0,'can_attack_multiplier':0.0},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'Petrochemical': ElementBuff(
        name='Petrochemical',
        duration=3.0,
        element='earth',
        multipliers={'speed_multiplier': 0.0,'can_attack_multiplier':0.0, 'all_resistance_multiplier': 0.9,},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'Fog': ElementBuff(
        name='Fog',
        duration=3.0,
        element='water',
        multipliers={'vision_radius_multiplier': 0.1},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'Vulnerable': ElementBuff(
        name='Vulnerable',
        duration=3.0,
        element='untyped',
        multipliers={'all_resistance_multiplier': -0.5,},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'Taser': ElementBuff(
        name='Taser',
        duration=3.0,
        element='electric',
        multipliers={'speed_multiplier': 0.0,'can_attack_multiplier': 0.0,},
        effect_per_second=lambda e: e.take_damage(max_hp_percentage_damage=10, element='electric') if hasattr(e, 'take_damage') else None,
        on_apply=None,
        on_remove=None,
    ),
    'Sandstorm': ElementBuff(
        name='Sandstorm',
        duration=3.0,
        element='earth',
        multipliers={'speed_multiplier': 0.7, 'vision_radius_multiplier': 0.5},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'Bleeding': ElementBuff(
        name='Bleeding',
        duration=3.0,
        element='untyped',
        multipliers={'defense_multiplier': 0.8,},
        effect_per_second=lambda e: e.take_damage(lose_hp_percentage_damage=10, element='untyped') if hasattr(e, 'take_damage') else None,
        on_apply=None,
        on_remove=None,
    ),
    'Backdraft ': ElementBuff(
        name='Backdraft ',
        duration=3.0,
        element='fire',
        multipliers={},
        effect_per_second=None,
        on_apply=lambda e: e.take_damage(max_hp_percentage_damage=20, element='fire') if hasattr(e, 'take_damage') else None,
        on_remove=None,
    ),
    'Annihilation': ElementBuff(
        name='Annihilation',
        duration=3.0,
        element='untyped',
        multipliers={},
        effect_per_second=None,
        on_apply=lambda e: e.take_damage(max_hp_percentage_damage=20, element='untyped') if hasattr(e, 'take_damage') else None,
        on_remove=None,
    ),
    'Enpty': ElementBuff(
        name='Enpty',
        duration=1.0,
        element='untyped',
        multipliers={},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
    'Untyped': ElementBuff(
        name='Untyped',
        duration=1.0,
        element='untyped',
        multipliers={},
        effect_per_second=None,
        on_apply=None,
        on_remove=None,
    ),
}


def apply_elemental_buff(entity: 'BuffableEntity', element: str, duration: float = 3.0, strength: float = 1.0) -> None:
    """
    Convenience function to apply a predefined elemental buff to an entity.
    Adjusts duration and strength as needed.
    """
    if element in ELEMENTAL_BUFFS:
        buff = ELEMENTAL_BUFFS[element].deepcopy()
        buff.duration = duration
        buff.strength = strength
        entity.add_buff(buff)
    else:
        print(f"Unknown element: {element}")


def get_elemental_interaction_description(attacker_element: str, defender_element: str) -> str:
    """
    Get a description of the elemental interaction based on the affinity table.
    """
    multiplier = ElementBuff('', 0, attacker_element, {}).get_affinity_multiplier(defender_element)
    if multiplier == AFFINITY_MULTIPLIER_WEAK:
        return f"{attacker_element} beats {defender_element} (1.5x damage)"
    elif multiplier == AFFINITY_MULTIPLIER_RESIST:
        return f"{defender_element} resists {attacker_element} (0.5x damage)"
    else:
        return f"{attacker_element} neutral to {defender_element} (1.0x damage)"