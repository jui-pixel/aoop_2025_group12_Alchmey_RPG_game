# src/entities/attack_entity.py
from typing import *
import pygame
import math
from .basic_entity import BasicEntity
from .buff.buff import Buff
from src.ecs.components import Combat

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
        
        # Attack Properties (kept for non-ECS fallback or properties not yet in Combat component)
        self._can_attack: bool = can_attack
        self._damage_to_element: Dict[str, float] = damage_to_element if damage_to_element is not None else {
            'untyped': 1.0, 'light': 1.0, 'dark': 1.0, 'metal': 1.0, 'wood': 1.0,
            'water': 1.0, 'fire': 1.0, 'earth': 1.0, 'ice': 1.0, 'electric': 1.0, 'wind': 1.0
        }
        
        # Collision Properties (kept for non-ECS fallback or properties not yet in Combat component)
        self.atk_element: str = atk_element
        self.damage: int = damage
        self.max_hp_percentage_damage: int = max_hp_percentage_damage
        self.current_hp_percentage_damage: int = current_hp_percentage_damage
        self.lose_hp_percentage_damage: int = lose_hp_percentage_damage
        self.cause_death: bool = cause_death
        self.buffs: List['Buff'] = [buff.deepcopy() for buff in buffs] if buffs else []
        self.collision_shape: str = shape
        
        # Penetration Properties (kept for non-ECS fallback or properties not yet in Combat component)
        self.max_penetration_count: int = max_penetration_count
        self.current_penetration_count: int = 0
        self.collision_cooldown: float = collision_cooldown
        self.collision_list: Dict[int, float] = {}
        
        # Explosion Properties (kept for non-ECS fallback or properties not yet in Combat component)
        self.explosion_range: float = explosion_range
        self.explosion_damage: int = explosion_damage
        self.explosion_element: str = explosion_element
        self.explosion_buffs: List['Buff'] = [buff.deepcopy() for buff in explosion_buffs] if explosion_buffs else []
        self.explosion_max_hp_percentage_damage = explosion_max_hp_percentage_damage
        self.explosion_current_hp_percentage_damage = explosion_current_hp_percentage_damage
        self.explosion_lose_hp_percentage_damage = explosion_lose_hp_percentage_damage

        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
             self.game.ecs_world.add_component(self.ecs_entity, Combat(
                 damage=damage,
                 can_attack=can_attack,
                 atk_element=atk_element,
                 damage_to_element=self._damage_to_element, # Use the initialized dict
                 max_penetration_count=max_penetration_count,
                 current_penetration_count=0,
                 collision_cooldown=collision_cooldown,
                 collision_list={},
                 explosion_range=explosion_range,
                 explosion_damage=explosion_damage,
                 explosion_element=explosion_element
             ))

    # Getters
    @property
    def can_attack(self) -> bool:
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            return self.game.ecs_world.component_for_entity(self.ecs_entity, Combat).can_attack
        return self._can_attack
    
    @property
    def damage_to_element(self) -> Dict[str, float]:
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            return self.game.ecs_world.component_for_entity(self.ecs_entity, Combat).damage_to_element
        return self._damage_to_element

    # Setters
    @can_attack.setter
    def can_attack(self, value: bool) -> None:
        self.set_can_attack(value)

    def set_can_attack(self, can_attack: bool) -> None:
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            self.game.ecs_world.component_for_entity(self.ecs_entity, Combat).can_attack = can_attack
        self._can_attack = can_attack
    
    def set_damage_multiplier(self, element: str, multiplier: float) -> None:
        # This will now use the property getter, which delegates to ECS if available
        if element in self.damage_to_element:
            if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
                self.game.ecs_world.component_for_entity(self.ecs_entity, Combat).damage_to_element[element] = max(0.0, multiplier)
            else:
                self._damage_to_element[element] = max(0.0, multiplier)
    
    def init(self) -> None:
        """Initialize collision-related properties."""
        self.current_penetration_count = 0
        self.collision_list.clear()
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat.current_penetration_count = 0
            combat.collision_list.clear()
    
    def collision_update(self, dt: float, current_time: float) -> None:
        """Update collision cooldowns."""
        # Sync local list with ECS list if needed, or just use ECS list
        c_list = self.collision_list
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            c_list = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat).collision_list

        if c_list:
            to_remove = []
            for key in c_list.keys():
                c_list[key] -= dt
                if c_list[key] <= 0:
                    to_remove.append(key)
            
            for key in to_remove:
                del c_list[key]
    
    def can_collide_with(self, other_entity: 'EntityInterface') -> bool:
        """Check if this entity can collide with another entity."""
        c_list = self.collision_list
        curr_pen = self.current_penetration_count
        max_pen = self.max_penetration_count
        
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            c_list = combat.collision_list
            curr_pen = combat.current_penetration_count
            max_pen = combat.max_penetration_count

        if other_entity.id in c_list:
            return False
        
        if max_pen > 0 and curr_pen >= max_pen:
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
        # Use the property getter for can_attack
        if not self.can_attack or not self.can_collide_with(target) or self.tag == target.tag:
            return False
        
        # Get combat component or use local attributes
        combat_data = None
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat_data = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat_data.collision_list[target.id] = combat_data.collision_cooldown
            combat_data.current_penetration_count += 1
        else:
            self.collision_list[target.id] = self.collision_cooldown
            self.current_penetration_count += 1
        
        # Apply damage with buff multiplier
        damage_mult = getattr(self, 'get_modifier', lambda x: 1.0)('damage_multiplier')
        
        # Get damage and element from combat_data or local attributes
        atk_element = combat_data.atk_element if combat_data else self.atk_element
        damage = combat_data.damage if combat_data else self.damage
        damage_to_element_map = combat_data.damage_to_element if combat_data else self.damage_to_element
        
        multiplier = damage_to_element_map.get(atk_element, 1.0)
        effective_damage = int(damage * multiplier * damage_mult)
        
        print(f"AttackEntity collision: base damage {damage}, element {atk_element}, multiplier {multiplier}, damage_mult {damage_mult}, effective damage {effective_damage}")
        if effective_damage > 0:
            killed, actual_damage = target.take_damage(
                factor=1.0,
                element=atk_element,
                base_damage=effective_damage,
                max_hp_percentage_damage=self.max_hp_percentage_damage, # Not in Combat component yet
                current_hp_percentage_damage=self.current_hp_percentage_damage, # Not in Combat component yet
                lose_hp_percentage_damage=self.lose_hp_percentage_damage, # Not in Combat component yet
                cause_death=self.cause_death # Not in Combat component yet
            )
            print(f"Collision damage: {actual_damage} to {target.__class__.__name__}")
        
        # Apply buffs
        if self.buffs and hasattr(target, 'add_buff'): # Not in Combat component yet
            for buff in self.buffs:
                target.add_buff(buff.deepcopy())
        
        # Trigger explosion
        explosion_range = combat_data.explosion_range if combat_data else self.explosion_range
        if explosion_range > 0 and entities:
            self.trigger_explosion(entities)
        
        return True
    
    def set_penetration_count(self, count: int) -> None:
        """Set the maximum penetration count."""
        self.max_penetration_count = count
        self.current_penetration_count = 0
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat.max_penetration_count = count
            combat.current_penetration_count = 0
    
    def reset_penetration(self) -> None:
        """Reset penetration count and collision list."""
        self.current_penetration_count = 0
        self.collision_list.clear()
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat.current_penetration_count = 0
            combat.collision_list.clear()
    
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
        
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat.explosion_range = range
            combat.explosion_damage = damage
            combat.explosion_element = element
    
    def trigger_explosion(self, entities: List['EntityInterface']) -> None:
        """Trigger explosion and damage nearby entities."""
        combat_data = None
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat_data = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)

        explosion_range = combat_data.explosion_range if combat_data else self.explosion_range
        if explosion_range <= 0:
            return
        
        explosion_center = (self.x + self.w / 2, self.y + self.h / 2)
        damage_mult = getattr(self, 'get_modifier', lambda x: 1.0)('damage_multiplier')
        
        for entity in entities:
            if not hasattr(entity, 'take_damage'):
                continue
            if self.tag == entity.tag:
                continue  # Prevent self-damage or friendly fire
            
            entity_center = (entity.x + entity.w / 2, entity.y + entity.h / 2)
            distance = math.sqrt(
                (explosion_center[0] - entity_center[0])**2 + 
                (explosion_center[1] - entity_center[1])**2
            )
            
            if distance <= explosion_range:
                explosion_element = combat_data.explosion_element if combat_data else self.explosion_element
                explosion_damage = combat_data.explosion_damage if combat_data else self.explosion_damage
                damage_to_element_map = combat_data.damage_to_element if combat_data else self.damage_to_element

                multiplier = damage_to_element_map.get(explosion_element, 1.0)
                effective_explosion_damage = int(explosion_damage * multiplier * damage_mult)
                killed, actual_damage = entity.take_damage(
                    factor=1.0,
                    element=explosion_element,
                    base_damage=effective_explosion_damage,
                    max_hp_percentage_damage=self.explosion_max_hp_percentage_damage, # Not in Combat component yet
                    current_hp_percentage_damage=self.explosion_current_hp_percentage_damage, # Not in Combat component yet
                    lose_hp_percentage_damage=self.explosion_lose_hp_percentage_damage, # Not in Combat component yet
                    cause_death=self.cause_death # Not in Combat component yet
                )
                print(f"Explosion damage: {actual_damage} to {entity.__class__.__name__}")
                
                if self.explosion_buffs and hasattr(entity, 'add_buff'): # Not in Combat component yet
                    for buff in self.explosion_buffs:
                        entity.add_buff(buff.deepcopy())

    def set_collision_cooldown(self, cooldown: float) -> None:
        """Set collision cooldown time."""
        self.collision_cooldown = cooldown
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            self.game.ecs_world.component_for_entity(self.ecs_entity, Combat).collision_cooldown = cooldown
    
    def get_penetration_remaining(self) -> int:
        """Get remaining penetration count."""
        curr = self.current_penetration_count
        max_p = self.max_penetration_count
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            curr = combat.current_penetration_count
            max_p = combat.max_penetration_count
        return max(0, max_p - curr)
    
    def can_penetrate(self) -> bool:
        """Check if entity can still penetrate."""
        curr = self.current_penetration_count
        max_p = self.max_penetration_count
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            
            for key in to_remove:
                del c_list[key]
    
    def can_collide_with(self, other_entity: 'EntityInterface') -> bool:
        """Check if this entity can collide with another entity."""
        c_list = self.collision_list
        curr_pen = self.current_penetration_count
        max_pen = self.max_penetration_count
        
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            c_list = combat.collision_list
            curr_pen = combat.current_penetration_count
            max_pen = combat.max_penetration_count

        if other_entity.id in c_list:
            return False
        
        if max_pen > 0 and curr_pen >= max_pen:
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
        # Use the property getter for can_attack
        if not self.can_attack or not self.can_collide_with(target) or self.tag == target.tag:
            return False
        
        # Get combat component or use local attributes
        combat_data = None
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat_data = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat_data.collision_list[target.id] = combat_data.collision_cooldown
            combat_data.current_penetration_count += 1
        else:
            self.collision_list[target.id] = self.collision_cooldown
            self.current_penetration_count += 1
        
        # Apply damage with buff multiplier
        damage_mult = getattr(self, 'get_modifier', lambda x: 1.0)('damage_multiplier')
        
        # Get damage and element from combat_data or local attributes
        atk_element = combat_data.atk_element if combat_data else self.atk_element
        damage = combat_data.damage if combat_data else self.damage
        damage_to_element_map = combat_data.damage_to_element if combat_data else self.damage_to_element
        
        multiplier = damage_to_element_map.get(atk_element, 1.0)
        effective_damage = int(damage * multiplier * damage_mult)
        
        print(f"AttackEntity collision: base damage {damage}, element {atk_element}, multiplier {multiplier}, damage_mult {damage_mult}, effective damage {effective_damage}")
        if effective_damage > 0:
            killed, actual_damage = target.take_damage(
                factor=1.0,
                element=atk_element,
                base_damage=effective_damage,
                max_hp_percentage_damage=self.max_hp_percentage_damage, # Not in Combat component yet
                current_hp_percentage_damage=self.current_hp_percentage_damage, # Not in Combat component yet
                lose_hp_percentage_damage=self.lose_hp_percentage_damage, # Not in Combat component yet
                cause_death=self.cause_death # Not in Combat component yet
            )
            print(f"Collision damage: {actual_damage} to {target.__class__.__name__}")
        
        # Apply buffs
        if self.buffs and hasattr(target, 'add_buff'): # Not in Combat component yet
            for buff in self.buffs:
                target.add_buff(buff.deepcopy())
        
        # Trigger explosion
        explosion_range = combat_data.explosion_range if combat_data else self.explosion_range
        if explosion_range > 0 and entities:
            self.trigger_explosion(entities)
        
        return True
    
    def set_penetration_count(self, count: int) -> None:
        """Set the maximum penetration count."""
        self.max_penetration_count = count
        self.current_penetration_count = 0
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat.max_penetration_count = count
            combat.current_penetration_count = 0
    
    def reset_penetration(self) -> None:
        """Reset penetration count and collision list."""
        self.current_penetration_count = 0
        self.collision_list.clear()
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat.current_penetration_count = 0
            combat.collision_list.clear()
    
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
        
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            combat.explosion_range = range
            combat.explosion_damage = damage
            combat.explosion_element = element
    
    def trigger_explosion(self, entities: List['EntityInterface']) -> None:
        """Trigger explosion and damage nearby entities."""
        combat_data = None
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat_data = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)

        explosion_range = combat_data.explosion_range if combat_data else self.explosion_range
        if explosion_range <= 0:
            return
        
        explosion_center = (self.x + self.w / 2, self.y + self.h / 2)
        damage_mult = getattr(self, 'get_modifier', lambda x: 1.0)('damage_multiplier')
        
        for entity in entities:
            if not hasattr(entity, 'take_damage'):
                continue
            if self.tag == entity.tag:
                continue  # Prevent self-damage or friendly fire
            
            entity_center = (entity.x + entity.w / 2, entity.y + entity.h / 2)
            distance = math.sqrt(
                (explosion_center[0] - entity_center[0])**2 + 
                (explosion_center[1] - entity_center[1])**2
            )
            
            if distance <= explosion_range:
                explosion_element = combat_data.explosion_element if combat_data else self.explosion_element
                explosion_damage = combat_data.explosion_damage if combat_data else self.explosion_damage
                damage_to_element_map = combat_data.damage_to_element if combat_data else self.damage_to_element

                multiplier = damage_to_element_map.get(explosion_element, 1.0)
                effective_explosion_damage = int(explosion_damage * multiplier * damage_mult)
                killed, actual_damage = entity.take_damage(
                    factor=1.0,
                    element=explosion_element,
                    base_damage=effective_explosion_damage,
                    max_hp_percentage_damage=self.explosion_max_hp_percentage_damage, # Not in Combat component yet
                    current_hp_percentage_damage=self.explosion_current_hp_percentage_damage, # Not in Combat component yet
                    lose_hp_percentage_damage=self.explosion_lose_hp_percentage_damage, # Not in Combat component yet
                    cause_death=self.cause_death # Not in Combat component yet
                )
                print(f"Explosion damage: {actual_damage} to {entity.__class__.__name__}")
                
                if self.explosion_buffs and hasattr(entity, 'add_buff'): # Not in Combat component yet
                    for buff in self.explosion_buffs:
                        entity.add_buff(buff.deepcopy())

    def set_collision_cooldown(self, cooldown: float) -> None:
        """Set collision cooldown time."""
        self.collision_cooldown = cooldown
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            self.game.ecs_world.component_for_entity(self.ecs_entity, Combat).collision_cooldown = cooldown
    
    def get_penetration_remaining(self) -> int:
        """Get remaining penetration count."""
        curr = self.current_penetration_count
        max_p = self.max_penetration_count
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            curr = combat.current_penetration_count
            max_p = combat.max_penetration_count
        return max(0, max_p - curr)
    
    def can_penetrate(self) -> bool:
        """Check if entity can still penetrate."""
        curr = self.current_penetration_count
        max_p = self.max_penetration_count
        if self.ecs_entity is not None and self.game and hasattr(self.game, 'ecs_world'):
            combat = self.game.ecs_world.component_for_entity(self.ecs_entity, Combat)
            curr = combat.current_penetration_count
            max_p = combat.max_penetration_count
        return max_p <= 0 or curr < max_p
    
    def update(self, dt, current_time):
        # Logic moved to CombatSystem
        pass