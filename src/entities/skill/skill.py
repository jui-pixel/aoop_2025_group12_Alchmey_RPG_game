
from typing import Optional, Dict, Tuple, List
from .abstract_skill import Skill
from .shoot_skill import ShootingSkill
from .buff_skill import BuffSkill
from ...config import TILE_SIZE



def create_skill_from_dict(data: Dict) -> Skill:
    if data['type'] == 'shooting':
        params = data['params']
        return ShootingSkill(
            name=data['name'],
            element=data['element'],
            energy_cost=20.0,
            element_buff_enable=params.get('elebuff', 0) > 0,
            bullet_damage=10 * (1 + 0.1 * params.get('damage', 0)),
            bullet_speed=3 * TILE_SIZE * (1 + 0.1 * params.get('speed', 0)),
            bullet_size=8,
            bullet_element=data['element'],
            max_penetration_count=params.get('penetration', 0),
            explosion_range=params.get('explosion', 0),
            # Assume other params 0
            bullet_max_hp_percentage_damage=0,
            bullet_current_hp_percentage_damage=0,
            bullet_lose_hp_percentage_damage=0,
            explosion_damage=0,
            explosion_max_hp_percentage_damage=0,
            explosion_current_hp_percentage_damage=0,
            explosion_lose_hp_percentage_damage=0,
            collision_cooldown=0.2,
            pass_wall=False
        )
    elif data['type'] == 'buff':
        params = data['params']
        return BuffSkill(
            name=data['name'],
            type='buff',
            element=data['element'],
            energy_cost=20.0,
            buff_duration_level=params.get('duration', 0),
            element_resistance_level=params.get('element_resistance', 0),
            counter_element_resistance_level=params.get('counter_element_resistance', 0),
            shield_level=params.get('shield', 0),
            remove_element_debuff=params.get('remove_element', 0) > 0,
            remove_counter_element_debuff=params.get('remove_counter', 0) > 0,
            avoid_level=params.get('avoid', 0),
            speed_level=params.get('speed', 0),
        )
    else:
        raise ValueError("Unknown skill type")