from typing import Dict, List, Optional, Callable
from buff import Buff
from buffable_entity import BuffableEntity

# Elemental affinities based on the game's interaction table (derived from combat_entity cycle and special affinities)
ELEMENT_CYCLE = ['metal', 'wood', 'earth', 'water', 'fire']  # Sequential weakness: metal -> wood -> earth -> water -> fire -> metal
SPECIAL_AFFINITIES = [
    ('earth', 'electric'),
    ('wood', 'wind'),
    ('fire', 'ice')
]
OPPOSITE_ELEMENTS = {'light': 'dark', 'dark': 'light'}

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
                 mergeable_elements: Optional[List[str]] = None):
        super().__init__(name, duration, element, multipliers, effect_per_second, on_apply, on_remove)
        self.strength = strength  # Amplifies effect based on elemental interaction
        self.mergeable_elements = mergeable_elements or []  # Elements this buff can merge with
    
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
            mergeable_elements=self.mergeable_elements.copy()
        )
    
    def get_affinity_multiplier(self, target_element: str) -> float:
        """
        Calculate affinity multiplier based on elemental interaction table.
        Returns 1.5 for weak (beats), 0.5 for strong (resists), 1.0 otherwise.
        """
        if self.element == 'untyped' or target_element == 'untyped':
            return NEUTRAL_MULTIPLIER
        
        # Opposite elements (light/dark)
        if (self.element == 'light' and target_element == 'dark') or \
           (self.element == 'dark' and target_element == 'light'):
            return AFFINITY_MULTIPLIER_WEAK
        
        # Cycle-based interactions
        if self.element in ELEMENT_CYCLE and target_element in ELEMENT_CYCLE:
            self_idx = ELEMENT_CYCLE.index(self.element)
            target_idx = ELEMENT_CYCLE.index(target_element)
            # If attacker beats defender (next in cycle)
            if (self_idx + 1) % len(ELEMENT_CYCLE) == target_idx:
                return AFFINITY_MULTIPLIER_WEAK
            # If defender resists attacker (previous in cycle)
            elif (target_idx + 1) % len(ELEMENT_CYCLE) == self_idx:
                return AFFINITY_MULTIPLIER_RESIST
        
        # Special affinities
        for attacker, defender in SPECIAL_AFFINITIES:
            if (self.element == attacker and target_element == defender):
                return AFFINITY_MULTIPLIER_WEAK
            elif (self.element == defender and target_element == attacker):
                return AFFINITY_MULTIPLIER_RESIST
        
        return NEUTRAL_MULTIPLIER
    
    def can_merge_with(self, other_buff: 'ElementBuff') -> bool:
        """
        Check if this buff can merge with another based on mergeable_elements.
        """
        return other_buff.element in self.mergeable_elements or self.element in other_buff.mergeable_elements


class ElementalBuffSynthesizer:
    """
    Handles synthesis and merging of elemental buffs based on the interaction table.
    Extends BuffSynthesizer to include elemental-specific merge rules.
    """
    
    def __init__(self):
        self.merge_rules = {
            # Example merge rules based on cycle and special affinities
            # Format: (element1, element2) -> new_element, new_multipliers
            ('fire', 'water'): ('steam', {'damage_multiplier': 0.8, 'speed_multiplier': 1.2}),  # Fire + Water = Steam (reduced damage, increased speed)
            ('earth', 'water'): ('mud', {'defense_multiplier': 1.5, 'speed_multiplier': 0.8}),  # Earth + Water = Mud (increased defense, reduced speed)
            ('fire', 'wood'): ('ash', {'health_multiplier': 0.7, 'damage_multiplier': 1.3}),   # Fire beats Wood -> Ash (reduced health, increased damage)
            ('light', 'dark'): ('balance', {'all_multipliers': 1.0}),  # Neutralizes opposites
            # Add more based on full interaction table
        }
        self.cycle_merge_bonus = 1.2  # Bonus multiplier for cycle-based merges
    
    def synthesize_elemental_buffs(self, buffs: List[ElementBuff], entity: BuffableEntity) -> None:
        """
        Synthesize elemental buffs based on merge rules.
        Checks for pairs that can merge and creates a new combined buff.
        """
        for i, buff1 in enumerate(buffs):
            for j, buff2 in enumerate(buffs[i+1:], i+1):
                if buff1.can_merge_with(buff2):
                    key = tuple(sorted([buff1.element, buff2.element]))
                    if key in self.merge_rules:
                        new_element, new_multipliers = self.merge_rules[key]
                        
                        # Calculate combined duration and strength
                        combined_duration = max(buff1.duration, buff2.duration)
                        combined_strength = (buff1.strength + buff2.strength) * self.cycle_merge_bonus if key[0] in ELEMENT_CYCLE and key[1] in ELEMENT_CYCLE else (buff1.strength + buff2.strength) / 2
                        
                        # Create synthesized buff
                        synthesized_buff = ElementBuff(
                            name=f"{new_element}_merged",
                            duration=combined_duration,
                            element=new_element,
                            multipliers={
                                **new_multipliers,  # Base from rule
                                'strength': combined_strength  # Apply strength
                            },
                            effect_per_second=lambda e: self._apply_merged_effect(e, new_element),
                            on_apply=lambda e: print(f"Applied merged {new_element} buff to {e.tag}"),
                            on_remove=lambda e: print(f"Removed merged {new_element} buff from {e.tag}"),
                            strength=combined_strength,
                            mergeable_elements=[elem for elem in ELEMENT_CYCLE if elem != new_element]  # Can merge with non-same elements
                        )
                        
                        # Remove original buffs and add synthesized one
                        entity.remove_buff(buff1)
                        entity.remove_buff(buff2)
                        entity.add_buff(synthesized_buff)
                        print(f"Merged {buff1.element} + {buff2.element} into {new_element}")
                        return  # Only one merge per update to avoid chains
    
    def _apply_merged_effect(self, entity: BuffableEntity, element: str) -> None:
        """
        Apply special effect for merged elemental buffs.
        """
        if element == 'steam':
            # Example: Steam reduces visibility or adds slipperiness (reduce speed temporarily)
            entity.modifiers['speed_multiplier'] *= 0.9
        elif element == 'mud':
            # Mud increases defense but slows movement
            entity.modifiers['defense_multiplier'] *= 1.1
        elif element == 'ash':
            # Ash causes ongoing damage over time
            if hasattr(entity, 'take_damage'):
                entity.take_damage(base_damage=5, element='fire', cause_death=False)
        # Add more merged effects based on interaction table


# Predefined Elemental Buffs based on interaction table
ELEMENTAL_BUFFS = {
    'fire': ElementBuff(
        name='FireBurn',
        duration=3.0,
        element='fire',
        multipliers={'damage_multiplier': 1.2, 'health_regen_per_second': -2.0},  # Damage over time
        effect_per_second=lambda e: e.take_damage(base_damage=10, element='fire') if hasattr(e, 'take_damage') else None,
        mergeable_elements=['water', 'wood', 'ice']
    ),
    'water': ElementBuff(
        name='WaterSoak',
        duration=4.0,
        element='water',
        multipliers={'defense_multiplier': 1.1, 'speed_multiplier': 0.9},
        mergeable_elements=['fire', 'earth']
    ),
    'earth': ElementBuff(
        name='EarthBind',
        duration=5.0,
        element='earth',
        multipliers={'defense_multiplier': 1.3, 'speed_multiplier': 0.7},
        effect_per_second=lambda e: print(f"{e.tag} is bound by earth!") if hasattr(e, 'tag') else None,
        mergeable_elements=['water', 'electric']
    ),
    'wood': ElementBuff(
        name='WoodGrowth',
        duration=6.0,
        element='wood',
        multipliers={'health_multiplier': 1.2, 'damage_multiplier': 1.1},
        mergeable_elements=['fire', 'metal']
    ),
    'metal': ElementBuff(
        name='MetalArmor',
        duration=4.0,
        element='metal',
        multipliers={'defense_multiplier': 1.4},
        mergeable_elements=['wood']
    ),
    'ice': ElementBuff(
        name='IceFreeze',
        duration=3.0,
        element='ice',
        multipliers={'speed_multiplier': 0.5},
        effect_per_second=lambda e: e.set_max_speed(e.base_max_speed * 0.8) if hasattr(e, 'set_max_speed') else None,
        mergeable_elements=['fire']
    ),
    'electric': ElementBuff(
        name='ElectricShock',
        duration=2.0,
        element='electric',
        multipliers={'damage_multiplier': 1.5},
        mergeable_elements=['earth']
    ),
    'wind': ElementBuff(
        name='WindGust',
        duration=3.0,
        element='wind',
        multipliers={'speed_multiplier': 1.3},
        mergeable_elements=['wood']
    ),
    'light': ElementBuff(
        name='LightBless',
        duration=5.0,
        element='light',
        multipliers={'all_multipliers': 1.1},  # Boost all stats
        mergeable_elements=['dark']
    ),
    'dark': ElementBuff(
        name='DarkCurse',
        duration=4.0,
        element='dark',
        multipliers={'damage_multiplier': 1.4, 'health_multiplier': 0.8},
        mergeable_elements=['light']
    )
}


def apply_elemental_buff(entity: BuffableEntity, element: str, duration: float = 3.0, strength: float = 1.0) -> None:
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