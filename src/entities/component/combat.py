"""
Combat Component Interface
Handles combat-related properties like HP, shield, resistances, and damage calculation.
"""

from typing import Dict, Optional, Tuple
from .entity_interface import ComponentInterface


class Combat():
    """
    Combat component that handles all combat-related properties:
    - HP system (current HP, max HP, base max HP)
    - Shield system (current shield, max shield)
    - Elemental resistances
    - Combat flags (can move, can attack, invulnerable, dodge rate)
    - Damage calculation
    """
    
    def __init__(self, entity: 'EntityInterface'):
        super().__init__(entity)
        # HP System
        self.base_max_hp: int = 100
        self.max_hp: int = 100
        self.current_hp: int = 100
        
        self.def_element = "untyped"
        
        # Shield System
        self.max_shield: int = 0
        self.current_shield: int = 0
        
        # Elemental Resistances
        self.resistances: Dict[str, float] = {
            'untyped': 0.0,
            'light': 0.0,
            'dark': 0.0,
            'metal': 0.0,
            'wood': 0.0,
            'water': 0.0,
            'fire': 0.0,
            'earth': 0.0,
            'ice': 0.0,
            'electric': 0.0,
            'wind': 0.0
        }
        
        self.damage_to_element: Dict[str, float] = {
            'untyped': 1.0,
            'light': 1.0,
            'dark': 1.0,
            'metal': 1.0,
            'wood': 1.0,
            'water': 1.0,
            'fire': 1.0,
            'earth': 1.0,
            'ice': 1.0,
            'electric': 1.0,
            'wind': 1.0
        }
        
        # Combat Flags
        self.can_move: bool = True
        self.can_attack: bool = True
        self.invulnerable: bool = False
        self.base_dodge_rate: float = 0.0
        self.dodge_rate: float = 0.0
        
        # Element
        self.element: str = 'untyped'
    
    def init(self) -> None:
        """Initialize combat component with default values."""
        self.current_hp = self.max_hp
        self.current_shield = self.max_shield
    
    def combat_update(self, dt: float, current_time: float) -> None:
        """Update combat component (shield regeneration, etc.)."""
        # Shield regeneration logic can be added here
        pass
    
    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, max_hp_percentage_damage: int = 0,
                        current_hp_percentage_damage: int = 0, lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """
        Apply damage to the entity, considering elemental resistance and affinity.
        Returns (killed, actual_damage).
        """
        # Check for dodge
        if self.dodge_rate > 0:
            import random
            if random.random() < self.dodge_rate:
                return False, 0
        
        # Calculate elemental affinity multiplier
        affinity_multiplier = self._calculate_affinity_multiplier(element)
        
        if max_hp_percentage_damage > 0:
            base_damage += self.max_hp * max_hp_percentage_damage / 100
        if current_hp_percentage_damage > 0:
            base_damage += self.current_hp * current_hp_percentage_damage / 100
        if lose_hp_percentage_damage > 0:
            base_damage += (self.max_hp - self.combat_component.current_hp) * lose_hp_percentage_damage / 100
        
        # Apply resistance
        resistance = self.resistances.get(element, 0.0)
        final_damage = max(1, int(base_damage * affinity_multiplier * (1.0 - resistance) * factor))
        
        # Apply damage to shield first
        if self.current_shield > 0:
            shield_damage = min(final_damage, self.current_shield)
            self.current_shield -= shield_damage
            final_damage -= shield_damage
            
            # If shield is depleted, remaining damage is lost
            if self.current_shield <= 0:
                final_damage = 0
        
        # Apply remaining damage to HP
        if final_damage > 0:
            remain_hp = self.current_hp - final_damage
            if remain_hp <= 0 and not cause_death:
                final_damage = self.current_hp - 1
                self.current_hp = 1
            else:
                self.current_hp = remain_hp
        
        # Check if entity is killed
        killed = self.current_hp <= 0
        if killed:
            self.current_hp = 0
        
        return killed, final_damage
    
    def _calculate_affinity_multiplier(self, element: str) -> float:
        """Calculate elemental affinity multiplier."""
        if element == 'untyped' or self.element == 'untyped':
            return 1.0
        
        # Light vs Dark
        if (element == 'light' and self.element == 'dark') or \
           (element == 'dark' and self.element == 'light'):
            return 1.5
        
        # Elemental cycle: Metal > Wood > Earth > Water > Fire > Metal
        cycle = ['metal', 'wood', 'earth', 'water', 'fire']
        if element in cycle and self.element in cycle:
            element_idx = cycle.index(element)
            self_idx = cycle.index(self.element)
            if (element_idx + 1) % len(cycle) == self_idx:
                return 1.5
        
        # Special affinities
        special_affinities = [
            ('earth', 'electric'),
            ('wood', 'wind'),
            ('fire', 'ice')
        ]
        
        for elem1, elem2 in special_affinities:
            if (element == elem1 and self.element == elem2) or \
               (element == elem2 and self.element == elem1):
                return 1.5
        
        return 1.0
    
    def heal(self, amount: int) -> None:
        """Heal the entity by the specified amount."""
        self.current_hp = min(self.max_hp, self.current_hp + amount)
    
    def add_shield(self, amount: int) -> None:
        """Add shield to the entity."""
        self.current_shield = min(self.max_shield, self.current_shield + amount)
    
    def set_max_hp(self, new_max_hp: int) -> None:
        """Set new maximum HP and adjust current HP accordingly."""
        old_max = self.max_hp
        self.max_hp = new_max_hp
        # Scale current HP proportionally
        if old_max > 0:
            self.current_hp = int(self.current_hp * new_max_hp / old_max)
        self.current_hp = min(self.max_hp, self.current_hp)
    
    def set_max_shield(self, new_max_shield: int) -> None:
        """Set new maximum shield."""
        self.max_shield = new_max_shield
        self.current_shield = min(self.max_shield, self.current_shield)
    
    def set_resistance(self, element: str, resistance: float) -> None:
        """Set resistance for a specific element."""
        if element in self.resistances:
            self.resistances[element] = max(0.0, min(1.0, resistance))
    
    def get_health_percentage(self) -> float:
        """Get current health as a percentage."""
        if self.max_hp <= 0:
            return 0.0
        return self.current_hp / self.max_hp
    
    def is_alive(self) -> bool:
        """Check if the entity is alive."""
        return self.current_hp > 0
