# src/entities/buffable_entity.py
from typing import Dict, List, Optional
import pygame
from .basic_entity import BasicEntity
from .buff.buff import Buff
from ..utils.elements import ELEMENTS
from .buff.element_buff import ELEMENTAL_BUFFS

class BuffSynthesizer:
    """Handles buff synthesis and combination logic."""
    
    def __init__(self):
        self.synthesis_rules = {
            ('Burn', 'Humid') : 'Fog',
            ('Burn', 'Mud') : 'Petrochemical',
            ('Burn', 'Freeze') : 'Vulnerable',
            ('Burn', 'Entangled') : 'Backdraft',
            ('Humid', 'Cold') : 'Freeze',
            ('Humid', 'Paralysis') : 'Taser',
            ('Humid', 'Dist') : 'Mud',
            ('Humid', 'Tear') : 'Bleeding',
            ('Disorder', 'Dist') : 'Sandstorm',
            ('Blind', 'Erosion') : 'Annihilation',
            ('Mud', 'Humid') : 'Enpty',
            ('Fog', 'Disorder') : 'Enpty',
            ('Entangled', 'Disorder') : 'Enpty',
            ('Tear', 'Dist') : 'Enpty',
            ('Tear', 'Entangled') : 'Enpty',
            ('Paralysis', 'Dist') : 'Enpty',
        }
    
    def synthesize_buffs(self, buffs: List['Buff'], entity: 'BuffableEntity') -> None:
        """Check for and apply buff synthesis rules."""
        buff_names = [buff.name for buff in buffs]
        
        for (buff1, buff2), result in self.synthesis_rules.items():
            if buff1 in buff_names and buff2 in buff_names:
                buff1_obj = next((b for b in buffs if b.name == buff1), None)
                buff2_obj = next((b for b in buffs if b.name == buff2), None)
                
                if buff1_obj and buff2_obj:
                    entity.remove_buff(buff1_obj)
                self.remove_buff(buff)
            else:
                self._apply_buff_effects(buff, dt)
        
        self._update_modifiers()
        
        if self.buff_synthesizer:
            self.buff_synthesizer.synthesize_buffs(self.buffs, self)
    
    def add_buff(self, buff: 'Buff') -> None:
        """
        Add a buff to the entity.
        If a buff with the same name exists, replace it with the longer duration one.
        """
        buff_copy = buff.deepcopy()
        
        for existing_buff in self.buffs[:]:
            if existing_buff.name == buff_copy.name:
                if buff_copy.duration > existing_buff.duration:
                    self.remove_buff(existing_buff)
                else:
                    return
        
        self.buffs.append(buff_copy)
        if buff_copy.on_apply:
            buff_copy.on_apply(self)
        
        print(f"Added buff: {buff_copy.name} (duration: {buff_copy.duration:.2f}s)")
    
    def remove_buff(self, buff: 'Buff') -> None:
        """Remove a buff from the entity."""
        if buff in self.buffs:
            self.buffs.remove(buff)
            if buff.on_remove:
                buff.on_remove(self)
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
        if buff.effect_per_second:
            buff.effect_time += dt
            if buff.effect_time - buff.last_effect_time >= 1.0:
                buff.effect_per_second(self)
                buff.last_effect_time = buff.effect_time
        
        health_regen = buff.multipliers.get('health_regen_per_second', 0.0)
        if health_regen != 0 and hasattr(self, 'current_hp') and hasattr(self, 'heal'):
            if health_regen > 0 or getattr(self, 'invulnerable', False) <= 0:
                self.heal(int(health_regen * dt))
    
    def _update_modifiers(self) -> None:
        """Recalculate all modifiers based on active buffs."""
        multiplier_keys = [k for k in self.modifiers if 'resistance' not in k.lower() and 'add' not in k.lower()]
        additive_keys = [k for k in self.modifiers if 'resistance' in k.lower() or 'add' in k.lower()]
        for key in multiplier_keys:
            self.modifiers[key] = 1.0
        for key in additive_keys:
            self.modifiers[key] = 0.0
        
        for buff in self.buffs:
            for modifier_name, value in buff.multipliers.items():
                if modifier_name in self.modifiers:
                    if 'resistance' in modifier_name or 'add' in modifier_name:
                        self.modifiers[modifier_name] += value
                    else:
                        self.modifiers[modifier_name] *= value
        
        self._apply_modifiers_to_entity()
    
    def _apply_modifiers_to_entity(self) -> None:
        """Apply calculated modifiers to the entity's attributes."""
        # Apply speed multiplier
        if hasattr(self, '_max_speed') and hasattr(self, '_base_max_speed'):
            speed_mult = self.modifiers.get('speed_multiplier', 1.0)
            self._max_speed = self._base_max_speed * speed_mult
            
        
        # Apply health multiplier
        if hasattr(self, 'set_max_hp') and hasattr(self, 'base_max_hp'):
            health_mult = self.modifiers.get('health_multiplier', 1.0)
            new_max_hp = int(self.base_max_hp * health_mult)
            self.set_max_hp(new_max_hp)
        
        # Apply defense multiplier
        if hasattr(self, '_defense') and hasattr(self, '_base_defense'):
            defense_mult = self.modifiers.get('defense_multiplier', 1.0)
            self._defense = int(self._base_defense * defense_mult)
        
        # Apply damage multiplier (for AttackEntity)
        if hasattr(self, 'damage'):
            damage_mult = self.modifiers.get('damage_multiplier', 1.0)
            # Assuming a base_damage exists or damage is the base value
            if hasattr(self, 'base_damage'):
                self.damage = int(self.base_damage * damage_mult)
            else:
                # If no base_damage, store it on first modification
                if not hasattr(self, '_base_damage'):
                    self._base_damage = self.damage
                self.damage = int(self._base_damage * damage_mult)
        
        # Apply vision radius multiplier (specific to Player)
        if hasattr(self, 'vision_radius'):
            vision_mult = self.modifiers.get('vision_radius_multiplier', 1.0)
            if not hasattr(self, '_base_vision_radius'):
                self._base_vision_radius = self.vision_radius
            self.vision_radius = int(self._base_vision_radius * vision_mult)
        
        # Apply can_attack multiplier
        if hasattr(self, 'set_can_attack'):
            can_attack_mult = self.modifiers.get('can_attack_multiplier', 1.0)
            self.set_can_attack(can_attack_mult >= 1.0)
        
        # Apply dodge rate additive
        if hasattr(self, 'dodge_rate'):
            dodge_add = self.modifiers.get('dodge_rate_add', 0.0)
            if not hasattr(self, '_base_dodge_rate'):
                self._base_dodge_rate = self.dodge_rate
            self.dodge_rate = max(0.0, min(1.0, self._base_dodge_rate + dodge_add))
        
        # Apply resistance modifiers
        if hasattr(self, '_resistances'):
            for element in ELEMENTS:
                mod_key = f'{element}_resistance_multiplier'
                add = self.modifiers.get(mod_key, 0.0)
                base_resistance = self._base_resistances.get(element, 0.0)
                self._resistances[element] = max(0.0, min(1.0, base_resistance + add))
            
            all_add = self.modifiers.get('all_resistance_multiplier', 0.0)
            for element in ELEMENTS:
                base_resistance = self._base_resistances.get(element, 0.0)
                self._resistances[element] = max(0.0, min(1.0, base_resistance + add + all_add))
    
    def get_modifier(self, name: str) -> float:
        """Get a specific modifier value."""
        return self.modifiers.get(name, 1.0 if 'resistance' not in name.lower() and 'add' not in name.lower() else 0.0)
    
    def get_active_buffs(self) -> List[str]:
        """Get list of active buff names."""
        return [buff.name for buff in self.buffs]
    
    def get_buff_count(self) -> int:
        """Get number of active buffs."""
        return len(self.buffs)