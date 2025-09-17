from typing import Tuple, Dict
from ..buff.buff import Buff
from .abstract_skill import Skill
from ...utils.elements import ELEMENTS, WEAKTABLE

class BuffSkill(Skill):
    def __init__(self, name: str, type: str, element: str, energy_cost: float,
                 buff_name: str = None, buff_duration_level: int = 0, element_resistance_level = 0,
                 counter_element_resistance_level = 0,
                 shield_level: int = 0, remove_element_debuff: bool = False, remove_counter_element_debuff: bool = False,
                 avoid_level: int = 0, speed_level: int = 0,):
        super().__init__(name, type, element, energy_cost)
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

        def on_apply(entity):
            if shield_level > 0:
                entity._current_shield += shield_level * 10
                entity.current_shield = min(entity.current_shield, entity.max_shield)
            if remove_element_debuff and hasattr(entity, 'remove_buff'):
                for buff in entity.buffs[:]:
                    if buff.element == self.element:
                        entity.remove_buff(buff)
            if remove_counter_element_debuff and hasattr(entity, 'remove_buff'):
                for buff in entity.buffs[:]:
                    if buff.element in counter_elements:
                        entity.remove_buff(buff)

        self.buff = Buff(
            name=buff_name ,
            duration=buff_duration_level + 1.0,
            element=self.element,
            multipliers=multipliers,
            effect_per_second=None,
            on_apply=on_apply,
            on_remove=None,
        )

    def activate(self, player: 'Player', game: 'Game', target_position: Tuple[float, float], current_time: float) -> None:
        self.last_used = current_time
        player.add_buff(self.buff)