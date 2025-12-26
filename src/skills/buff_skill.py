# src/entities/skill/buff_skill.py
from typing import TYPE_CHECKING, Tuple, Dict
import esper
from src.ecs.components import Buffs
from ..buffs.buff import Buff
from .abstract_skill import Skill
from ..utils.elements import ELEMENTS, WEAKTABLE

class BuffSkill(Skill):
    def __init__(self, name: str, type: str, element: str, energy_cost: float,
                 buff_name: str = None, buff_duration_level: int = 0, element_resistance_level = 0,
                 counter_element_resistance_level = 0,
                 shield_level: int = 0, remove_element_debuff: bool = False, remove_counter_element_debuff: bool = False,
                 avoid_level: int = 0, speed_level: int = 0,):
        super().__init__(name, type, element, energy_cost)
        buff_name = buff_name if buff_name else f"{name}_buff"
        counter_elements = [strong for strong, weak in WEAKTABLE if weak == self.element]
        multipliers = {}
        if element_resistance_level > 0:
            multipliers[f'{self.element}_resistance_multiplier'] = element_resistance_level * 0.1
        if counter_element_resistance_level > 0:
            for counter_element in counter_elements:
                multipliers[f'{counter_element}_resistance_multiplier'] = counter_element_resistance_level * 0.15
        if avoid_level > 0:
            multipliers['dodge_rate_add'] = avoid_level * 0.05
        if speed_level > 0:
            multipliers['speed_multiplier'] = 1 + speed_level * 0.1

        # Store shield level for ECS application
        self.shield_level = shield_level
        self.remove_element_debuff = remove_element_debuff
        self.remove_counter_element_debuff = remove_counter_element_debuff
        self.counter_elements = counter_elements

        def on_apply(entity_id):
            """Apply buff effects using ECS systems"""
            import esper
            from src.ecs.components import Health, Buffs
            from src.ecs.systems import HealthSystem
            
            # Apply shield using HealthSystem
            if self.shield_level > 0:
                health_system = esper.get_processor(HealthSystem)
                if health_system:
                    shield_amount = self.shield_level * 10
                    health_system.add_shield(entity_id, shield_amount)
                    print(f"Applied {shield_amount} shield to entity {entity_id}")
            
            # Remove debuffs if configured
            if esper.has_component(entity_id, Buffs):
                buffs_comp = esper.component_for_entity(entity_id, Buffs)
                
                if self.remove_element_debuff:
                    # Remove buffs of the same element
                    to_remove = [buff for buff in buffs_comp.active_buffs if buff.element == self.element]
                    for buff in to_remove:
                        if buff.on_remove:
                            buff.on_remove(entity_id)
                    buffs_comp.active_buffs = [
                        buff for buff in buffs_comp.active_buffs 
                        if buff.element != self.element
                    ]
                    print(f"Removed {self.element} debuffs from entity {entity_id}")
                
                if self.remove_counter_element_debuff:
                    # Remove counter-element debuffs
                    to_remove = [buff for buff in buffs_comp.active_buffs if buff.element in self.counter_elements]
                    for buff in to_remove:
                        if buff.on_remove:
                            buff.on_remove(entity_id)
                    buffs_comp.active_buffs = [
                        buff for buff in buffs_comp.active_buffs 
                        if buff.element not in self.counter_elements
                    ]
                    print(f"Removed counter-element debuffs from entity {entity_id}")
                from src.ecs.systems import BuffSystem
                buff_system = esper.get_processor(BuffSystem)
                if buff_system:
                    buff_system._update_modifiers(entity_id, buffs_comp)

        def on_remove(entity_id):
            """Cleanup when buff is removed (if needed)"""
            pass
        
        self.buff = Buff(
            name=buff_name,
            duration=buff_duration_level + 1.0,
            element=self.element,
            multipliers=multipliers,
            effect_per_second=None,
            on_apply=on_apply,
            on_remove=on_remove,
        )

    def activate(self, player: 'Player', game: 'Game', target_position: Tuple[float, float], current_time: float) -> None:
        """Activate the buff skill using ECS system"""
        self.last_used = current_time
        print(f"Activating BuffSkill '{self.name}' for player at time {current_time}")
        # Use player's ECS entity ID to apply buff
        import esper
        from src.ecs.components import Buffs
        import copy
        
        player_entity_id = player.ecs_entity
        
        if esper.has_component(player_entity_id, Buffs):
            buffs_comp = esper.component_for_entity(player_entity_id, Buffs)
            
            # Check if buff with same name already exists
            existing_buff = None
            for buff in buffs_comp.active_buffs:
                if buff.name == self.buff.name:
                    existing_buff = buff
                    break
            
            if existing_buff:
                # Refresh duration instead of stacking
                existing_buff.duration = self.buff.duration
                print(f"Refreshed buff '{self.buff.name}' duration to {self.buff.duration}s on player entity {player_entity_id}")
            else:
                # Add new buff
                buff_copy = copy.deepcopy(self.buff)
                buffs_comp.active_buffs.append(buff_copy)
                buff_copy.on_apply(player_entity_id)
                print(f"Applied buff '{buff_copy.name}' to player entity {player_entity_id}")
        else:
            print(f"Warning: Player entity {player_entity_id} does not have Buffs component")
