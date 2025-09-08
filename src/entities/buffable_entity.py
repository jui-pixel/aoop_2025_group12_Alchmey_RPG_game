from typing import Dict, List, Optional
import pygame
from basic_entity import BasicEntity
from buff import Buff

class BuffableEntity(BasicEntity):
    """
    Entity class that handles all buff-related functionality:
    - Buff management (add, remove, update)
    - Modifier calculation
    - Effect application
    - Buff synthesis
    """
    
    def __init__(self,
                 x: float = 0.0,
                 y: float = 0.0,
                 w: int = 32,
                 h: int = 32,
                 image: Optional[pygame.Surface] = None,
                 shape: str = "rect",
                 game: 'Game' = None,
                 tag: str = ""):
        super().__init__(x, y, w, h, image, shape, game, tag)
        self.buffable: bool = True
        self.buffs: List['Buff'] = []
        self.modifiers: Dict[str, float] = {
            'speed_multiplier': 1.0,
            'health_multiplier': 1.0,
            'defense_multiplier': 1.0,
            'damage_multiplier': 1.0,
            'vision_radius_multiplier': 1.0
        }
        self.buff_synthesizer: Optional['BuffSynthesizer'] = BuffSynthesizer()
    
    def init(self) -> None:
        """Initialize buff-related properties."""
        self.buffs = []
        self.modifiers = {key: 1.0 for key in self.modifiers}
    
    def update(self, dt: float, current_time: float) -> None:
        """Update all active buffs and recalculate modifiers."""
        for buff in self.buffs[:]:
            buff.duration -= dt
            if buff.duration <= 0:
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
        for key in self.modifiers:
            self.modifiers[key] = 1.0
        
        for buff in self.buffs:
            for modifier_name, value in buff.multipliers.items():
                if modifier_name in self.modifiers:
                    if 'multiplier' in modifier_name:
                        self.modifiers[modifier_name] *= value
                    else:
                        self.modifiers[modifier_name] += value
        
        self._apply_modifiers_to_entity()
    
    def _apply_modifiers_to_entity(self) -> None:
        """Apply calculated modifiers to the entity's attributes."""
        if hasattr(self, 'set_max_speed') and hasattr(self, 'base_max_speed'):
            speed_mult = self.modifiers.get('speed_multiplier', 1.0)
            self.set_max_speed(self.base_max_speed * speed_mult)
        
        if hasattr(self, 'set_max_hp') and hasattr(self, 'base_max_hp'):
            health_mult = self.modifiers.get('health_multiplier', 1.0)
            new_max_hp = int(self.base_max_hp * health_mult)
            self.set_max_hp(new_max_hp)
    
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
            ('Humid', 'Cold'): 'Freeze',
            ('Humid', 'Dust'): 'Mud',
            ('Mud', 'Burn'): 'Petrochemical'
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
                    entity.remove_buff(buff2_obj)
                    
                    # Create a new synthesized buff (example implementation)
                    synthesized_buff = Buff(
                        name=result,
                        duration=max(buff1_obj.duration, buff2_obj.duration),
                        element='untyped',
                        multipliers={'health_regen_per_second': 5.0}  # Example effect
                    )
                    entity.add_buff(synthesized_buff)
                    print(f"Synthesized {buff1} + {buff2} = {result}")
                    break