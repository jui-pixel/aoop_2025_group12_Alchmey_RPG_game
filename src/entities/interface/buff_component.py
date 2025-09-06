"""
Buff Component Interface
Handles buff management, modifiers, and effects.
"""

from typing import Dict, List, Optional, Any
import copy
from .entity_interface import ComponentInterface


class BuffComponent(ComponentInterface):
    """
    Buff component that handles all buff-related functionality:
    - Buff management (add, remove, update)
    - Modifier calculation
    - Effect application
    - Buff synthesis
    """
    
    def __init__(self, entity: 'EntityInterface'):
        super().__init__(entity)
        self.buffs: List['Buff'] = []
        self.modifiers: Dict[str, float] = {
            'speed_multiplier': 1.0,
            'health_multiplier': 1.0,
            'defense_multiplier': 1.0,
            'damage_multiplier': 1.0,
            'vision_radius_multiplier': 1.0
        }
        self.buff_synthesizer: Optional['BuffSynthesizer'] = None
    
    def init(self) -> None:
        """Initialize buff component."""
        self.buffs = []
        self.modifiers = {key: 1.0 for key in self.modifiers.keys()}
    
    def update(self, dt: float, current_time: float) -> None:
        """Update all active buffs and recalculate modifiers."""
        # Update buff durations and effects
        for buff in self.buffs[:]:  # Use slice to avoid modification during iteration
            buff.remaining_time -= dt
            if buff.remaining_time <= 0:
                self.remove_buff(buff)
            else:
                # Apply ongoing effects
                self._apply_buff_effects(buff, dt)
        
        # Recalculate modifiers
        self._update_modifiers()
        
        # Apply buff synthesis
        if self.buff_synthesizer:
            self.buff_synthesizer.synthesize_buffs(self.buffs, self.entity)
    
    def add_buff(self, buff: 'Buff') -> None:
        """
        Add a buff to the entity.
        If a buff with the same name exists, replace it with the longer duration one.
        """
        buff_copy = copy.deepcopy(buff)
        
        # Check for existing buff with same name
        for existing_buff in self.buffs[:]:
            if existing_buff.name == buff_copy.name:
                # If new buff has longer duration, replace the old one
                if buff_copy.remaining_time > existing_buff.remaining_time:
                    self.remove_buff(existing_buff)
                else:
                    return  # Keep the existing buff
        
        # Add the new buff
        self.buffs.append(buff_copy)
        if buff_copy.on_apply:
            buff_copy.on_apply(self.entity)
        
        print(f"Added buff: {buff_copy.name} (duration: {buff_copy.remaining_time:.2f}s)")
    
    def remove_buff(self, buff: 'Buff') -> None:
        """Remove a buff from the entity."""
        if buff in self.buffs:
            self.buffs.remove(buff)
            if buff.on_remove:
                buff.on_remove(self.entity)
            print(f"Removed buff: {buff.name}")
    
    def remove_buff_by_name(self, name: str) -> bool:
        """Remove a buff by name. Returns True if buff was found and removed."""
        for buff in self.buffs[:]:
            if buff.name == name:
                self.remove_buff(buff)
                return True
        return False
    
    def has_buff(self, name: str) -> bool:
        """Check if entity has a specific buff."""
        return any(buff.name == name for buff in self.buffs)
    
    def get_buff(self, name: str) -> Optional['Buff']:
        """Get a buff by name."""
        for buff in self.buffs:
            if buff.name == name:
                return buff
        return None
    
    def clear_buffs(self) -> None:
        """Remove all buffs."""
        for buff in self.buffs[:]:
            self.remove_buff(buff)
    
    def _apply_buff_effects(self, buff: 'Buff', dt: float) -> None:
        """Apply ongoing effects of a buff."""
        effects = buff.effects or {}
        
        # Health regeneration
        health_regen = effects.get('health_regen_per_second', 0.0)
        if health_regen != 0 and self.entity.combat_component:
            if health_regen > 0 or self.entity.combat_component.invulnerable <= 0:
                self.entity.combat_component.heal(int(health_regen * dt))
        
        # Other ongoing effects can be added here
        # e.g., damage over time, speed changes, etc.
    
    def _update_modifiers(self) -> None:
        """Recalculate all modifiers based on active buffs."""
        # Reset modifiers
        for key in self.modifiers:
            self.modifiers[key] = 1.0
        
        # Apply buff effects
        for buff in self.buffs:
            effects = buff.effects or {}
            for modifier_name, value in effects.items():
                if modifier_name in self.modifiers:
                    if 'multiplier' in modifier_name:
                        self.modifiers[modifier_name] *= value
                    else:
                        self.modifiers[modifier_name] += value
        
        # Apply modifiers to entity components
        self._apply_modifiers_to_entity()
    
    def _apply_modifiers_to_entity(self) -> None:
        """Apply calculated modifiers to the entity's components."""
        # Apply to movement component
        if self.entity.movement_component:
            speed_mult = self.modifiers.get('speed_multiplier', 1.0)
            self.entity.movement_component.set_max_speed(
                self.entity.movement_component.base_max_speed * speed_mult
            )
        
        # Apply to combat component
        if self.entity.combat_component:
            health_mult = self.modifiers.get('health_multiplier', 1.0)
            if health_mult != 1.0:
                new_max_hp = int(self.entity.combat_component.base_max_hp * health_mult)
                self.entity.combat_component.set_max_hp(new_max_hp)
            
            defense_mult = self.modifiers.get('defense_multiplier', 1.0)
            # Defense multiplier can be applied here if needed
    
    def get_modifier(self, name: str) -> float:
        """Get a specific modifier value."""
        return self.modifiers.get(name, 1.0)
    
    def get_active_buffs(self) -> List[str]:
        """Get list of active buff names."""
        return [buff.name for buff in self.buffs]
    
    def get_buff_count(self) -> int:
        """Get number of active buffs."""
        return len(self.buffs)


class BuffSynthesizer:
    """Handles buff synthesis and combination logic."""
    
    def __init__(self):
        self.synthesis_rules = {
            # Define synthesis rules here
            # e.g., ('Humid', 'Cold'): 'Freeze',
            #       ('Humid', 'Dist'): 'Mud',
            #       ('Mud', 'Burn'): 'Petrochemical'
        }
    
    def synthesize_buffs(self, buffs: List['Buff'], entity: 'EntityInterface') -> None:
        """Check for and apply buff synthesis rules."""
        buff_names = [buff.name for buff in buffs]
        
        for (buff1, buff2), result in self.synthesis_rules.items():
            if buff1 in buff_names and buff2 in buff_names:
                # Find the buffs to remove
                buff1_obj = next((b for b in buffs if b.name == buff1), None)
                buff2_obj = next((b for b in buffs if b.name == buff2), None)
                
                if buff1_obj and buff2_obj:
                    # Remove the original buffs
                    entity.buff_component.remove_buff(buff1_obj)
                    entity.buff_component.remove_buff(buff2_obj)
                    
                    # Add the synthesized buff
                    # This would need to be implemented based on your buff system
                    print(f"Synthesized {buff1} + {buff2} = {result}")
                    break  # Only apply one synthesis per update
