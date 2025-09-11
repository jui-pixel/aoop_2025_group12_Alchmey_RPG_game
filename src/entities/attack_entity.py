from typing import *
import pygame
import math
from .basic_entity import BasicEntity
from .buff.buff import Buff

class AttackEntity(BasicEntity):
    def __init__(self,
                 x: float = 0.0,
                 y: float = 0.0,
                 w: int = 32,
                 h: int = 32,
                 image: Optional[pygame.Surface] = None,
                 shape: str = "rect",
                 game: 'Game' = None,
                 tag: str = "",
                 can_attack: bool = True,
                 damage_to_element: Optional[Dict[str, float]] = None,
                 atk_element: str = "untyped",
                 damage: int = 0,
                 max_hp_percentage_damage: int = 0,
                 current_hp_percentage_damage: int = 0,
                 lose_hp_percentage_damage: int = 0,
                 cause_death: bool = True,
                 buffs: List['Buff'] = None,
                 max_penetration_count: int = 0,
                 collision_cooldown: float = 0.2,
                 explosion_range: float = 0.0,
                 explosion_damage: int = 0,
                 explosion_element: str = "untyped",
                 explosion_buffs: List['Buff'] = None,
                 explosion_max_hp_percentage_damage: int = 0,
                 explosion_current_hp_percentage_damage: int = 0,
                 explosion_lose_hp_percentage_damage: int = 0,
                 init_basic: bool = True):
        if init_basic:
            super().__init__(x, y, w, h, image, shape, game, tag)
        
        # Attack Properties
        self._can_attack: bool = can_attack
        self._damage_to_element: Dict[str, float] = damage_to_element if damage_to_element is not None else {
            'untyped': 1.0, 'light': 1.0, 'dark': 1.0, 'metal': 1.0, 'wood': 1.0,
            'water': 1.0, 'fire': 1.0, 'earth': 1.0, 'ice': 1.0, 'electric': 1.0, 'wind': 1.0
        }
        
        # Collision Properties
        self.atk_element: str = atk_element
        self.damage: int = damage
        self.max_hp_percentage_damage: int = max_hp_percentage_damage
        self.current_hp_percentage_damage: int = current_hp_percentage_damage
        self.lose_hp_percentage_damage: int = lose_hp_percentage_damage
        self.cause_death: bool = cause_death
        self.buffs: List['Buff'] = [buff.deepcopy() for buff in buffs] if buffs else []
        self.collision_shape: str = shape
        
        # Penetration Properties
        self.max_penetration_count: int = max_penetration_count
        self.current_penetration_count: int = 0
        self.collision_cooldown: float = collision_cooldown
        self.collision_list: Dict[int, float] = {}
        
        # Explosion Properties
        self.explosion_range: float = explosion_range
        self.explosion_damage: int = explosion_damage
        self.explosion_element: str = explosion_element
        self.explosion_buffs: List['Buff'] = [buff.deepcopy() for buff in explosion_buffs] if explosion_buffs else []
        # 注意: 原代碼有 explosion_max_hp_percentage_damage 等，但未定義；假設添加
        self.explosion_max_hp_percentage_damage = explosion_max_hp_percentage_damage
        self.explosion_current_hp_percentage_damage = explosion_current_hp_percentage_damage
        self.explosion_lose_hp_percentage_damage = explosion_lose_hp_percentage_damage

    # Getters
    @property
    def can_attack(self) -> bool:
        return self._can_attack
    
    @property
    def damage_to_element(self) -> Dict[str, float]:
        return self._damage_to_element

    # Setters
    @can_attack.setter
    def can_attack(self, value: bool) -> None:
        self.set_can_attack(value)

    def set_can_attack(self, can_attack: bool) -> None:
        self._can_attack = can_attack
    
    def set_damage_multiplier(self, element: str, multiplier: float) -> None:
        if element in self._damage_to_element:
            self._damage_to_element[element] = max(0.0, multiplier)
    
    def init(self) -> None:
        """Initialize collision-related properties."""
        self.current_penetration_count = 0
        self.collision_list.clear()
    
    def collision_update(self, dt: float, current_time: float) -> None:
        """Update collision cooldowns."""
        if self.collision_list:
            to_remove = []
            for key in self.collision_list.keys():
                self.collision_list[key] -= dt
                if self.collision_list[key] <= 0:
                    to_remove.append(key)
            
            for key in to_remove:
                del self.collision_list[key]
    
    def can_collide_with(self, other_entity: 'EntityInterface') -> bool:
        """Check if this entity can collide with another entity."""
        if other_entity.id in self.collision_list:
            return False
        
        if self.max_penetration_count > 0 and self.current_penetration_count >= self.max_penetration_count:
            return False
        
        return True
    
    def check_collision(self, other_entity: 'EntityInterface') -> bool:
        """Check if this entity is colliding with another entity."""
        if not other_entity:
            return False
        
        rect1 = self.get_rect()
        rect2 = other_entity.get_rect()
        
        return rect1.colliderect(rect2)
    
    def collision(self, target: 'EntityInterface', entities: List['EntityInterface'] = None) -> bool:
        """
        Handle collision with another entity, applying damage, buffs, and triggering explosion if applicable.
        Returns True if collision was processed, False otherwise.
        """
        if not self.can_attack or not self.can_collide_with(target) or self.tag == target.tag:
            return False
        
        self.collision_list[target.id] = self.collision_cooldown
        self.current_penetration_count += 1
        
        # Apply damage with buff multiplier
        damage_mult = getattr(self, 'get_modifier', lambda x: 1.0)('damage_multiplier')
        multiplier = self._damage_to_element.get(self.atk_element, 1.0)
        effective_damage = int(self.damage * multiplier * damage_mult)
        
        if effective_damage > 0:
            killed, actual_damage = target.take_damage(
                factor=1.0,
                element=self.atk_element,
                base_damage=effective_damage,
                max_hp_percentage_damage=self.max_hp_percentage_damage,
                current_hp_percentage_damage=self.current_hp_percentage_damage,
                lose_hp_percentage_damage=self.lose_hp_percentage_damage,
                cause_death=self.cause_death
            )
            print(f"Collision damage: {actual_damage} to {target.__class__.__name__}")
        
        # Apply buffs
        if self.buffs and hasattr(target, 'add_buff'):
            for buff in self.buffs:
                target.add_buff(buff.deepcopy())
        
        # Trigger explosion
        if self.explosion_range > 0 and entities:
            self.trigger_explosion(entities)
        
        return True
    
    def set_penetration_count(self, count: int) -> None:
        """Set the maximum penetration count."""
        self.max_penetration_count = count
        self.current_penetration_count = 0
    
    def reset_penetration(self) -> None:
        """Reset penetration count and collision list."""
        self.current_penetration_count = 0
        self.collision_list.clear()
    
    def set_explosion_properties(self, range: float, damage: int, element: str,
                                max_hp_percentage_damage: int = 0, 
                                current_hp_percentage_damage: int = 0,
                                lose_hp_percentage_damage: int = 0,
                                buffs: List['Buff'] = None) -> None:
        """Set explosion properties."""
        self.explosion_range = range
        self.explosion_damage = damage
        self.explosion_element = element
        self.explosion_max_hp_percentage_damage = max_hp_percentage_damage
        self.explosion_current_hp_percentage_damage = current_hp_percentage_damage
        self.explosion_lose_hp_percentage_damage = lose_hp_percentage_damage
        self.explosion_buffs = [buff.deepcopy() for buff in buffs] if buffs else []
    
    def trigger_explosion(self, entities: List['EntityInterface']) -> None:
        """Trigger explosion and damage nearby entities."""
        if self.explosion_range <= 0:
            return
        
        explosion_center = (self.x + self.w / 2, self.y + self.h / 2)
        damage_mult = getattr(self, 'get_modifier', lambda x: 1.0)('damage_multiplier')
        
        for entity in entities:
            if not hasattr(entity, 'take_damage'):
                continue
            
            entity_center = (entity.x + entity.w / 2, entity.y + entity.h / 2)
            distance = math.sqrt(
                (explosion_center[0] - entity_center[0])**2 + 
                (explosion_center[1] - entity_center[1])**2
            )
            
            if distance <= self.explosion_range:
                multiplier = self._damage_to_element.get(self.explosion_element, 1.0)
                effective_explosion_damage = int(self.explosion_damage * multiplier * damage_mult)
                killed, actual_damage = entity.take_damage(
                    factor=1.0,
                    element=self.explosion_element,
                    base_damage=effective_explosion_damage,
                    max_hp_percentage_damage=self.explosion_max_hp_percentage_damage,
                    current_hp_percentage_damage=self.explosion_current_hp_percentage_damage,
                    lose_hp_percentage_damage=self.explosion_lose_hp_percentage_damage,
                    cause_death=self.cause_death
                )
                print(f"Explosion damage: {actual_damage} to {entity.__class__.__name__}")
                
                if self.explosion_buffs and hasattr(entity, 'add_buff'):
                    for buff in self.explosion_buffs:
                        entity.add_buff(buff.deepcopy())

    def set_collision_cooldown(self, cooldown: float) -> None:
        """Set collision cooldown time."""
        self.collision_cooldown = cooldown
    
    def get_penetration_remaining(self) -> int:
        """Get remaining penetration count."""
        return max(0, self.max_penetration_count - self.current_penetration_count)
    
    def can_penetrate(self) -> bool:
        """Check if entity can still penetrate."""
        return self.max_penetration_count <= 0 or self.current_penetration_count < self.max_penetration_count