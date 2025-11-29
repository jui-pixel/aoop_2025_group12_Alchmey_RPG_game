# src/entities/skill/skill.py
from typing import Optional, Dict, Tuple, List
from .abstract_skill import Skill
from .shoot_skill import ShootingSkill
from .buff_skill import BuffSkill
from ..config import TILE_SIZE



def create_skill_from_dict(data: Dict) -> Optional['Skill']:
        """Create a skill instance from a dictionary.

        Args:
            data: Dictionary containing skill data with 'name', 'type', 'element', and 'params'.

        Returns:
            Optional[Skill]: The created skill instance or None if type is unknown.
        """
        name = data.get('name')
        skill_type = data.get('type')
        element = data.get('element', 'untyped')
        params = data.get('params', {})
        energy_cost = params.get('energy_cost', 20.0)

        if skill_type == 'shooting':
            return ShootingSkill(
                name=name,
                element=element,
                energy_cost=energy_cost,
                damage_level=params.get('damage', 0),
                penetration_level=params.get('penetration', 0),
                elebuff_level=params.get('elebuff', 0),
                explosion_level=params.get('explosion', 0),
                speed_level=params.get('speed', 0)
            )
        elif skill_type == 'buff':
            return BuffSkill(
                name=name,
                type=skill_type,
                element=element,
                buff_name=params.get('sub_type', None),
                energy_cost=energy_cost,
                buff_duration_level=params.get('duration', 0),
                element_resistance_level=params.get('element_resistance', 0),
                counter_element_resistance_level=params.get('counter_element_resistance', 0),
                shield_level=params.get('shield', 0),
                remove_element_debuff=params.get('remove_element', 0) > 0,
                remove_counter_element_debuff=params.get('remove_counter', 0) > 0,
                avoid_level=params.get('avoid', 0),
                speed_level=params.get('speed', 0)
            )
        else:
            print(f"StorageManager: Unknown skill type {skill_type}")
            return None