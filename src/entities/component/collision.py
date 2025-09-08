"""
Collision Component Interface
Handles collision detection, penetration, and explosion mechanics.
"""

from typing import List, Dict, Optional, Tuple, Set
import math
import pygame

class Collision():
    """
    Collision component that handles all collision-related functionality:
    - Collision detection and response
    - Penetration mechanics
    - Explosion mechanics
    - Collision cooldown and tracking
    """
    
    def __init__(self):
        # Collision properties
        self.atk_element: str = 'untyped'
        self.damage: int = 0
        self.max_hp_percentage_damage: int = 0
        self.current_hp_percentage_damage: int = 0
        self.lose_hp_percentage_damage: int = 0                
        self.cause_death: bool = True
        self.buffs: List['Buff'] = []
        self.collision_shape: str = 'rectangle'  # Collision detection shape
        
        # Penetration properties
        self.max_penetration_count: int = 0
        self.current_penetration_count: int = 0
        self.collision_cooldown: float = 0.2  # Cooldown between collisions
        self.collision_list: Dict[int:float] = {}  # List of entities already collided with
        
        # Explosion properties
        self.explosion_range: float = 0.0
        self.explosion_damage: int = 0
        self.explosion_element: str = 'untyped'
        self.explosion_buffs: List['Buff'] = []
    
    def init(self) -> None:
        """Initialize collision component."""
        self.current_penetration_count = 0
        self.collision_list.clear()
    
    def collision_update(self, dt: float, current_time: float) -> None:
        """Update collision component (cooldown, etc.)."""
        # Update collision cooldown
        if self.collision_list:
            to_remove = []
            for key in self.collision_list.keys:
                self.collision_list[key] -= dt
                if self.collision_list[key] <= 0:
                    to_remove.append(key)
            
            for key in to_remove:
                del self.collision_list[key]
    
    def can_collide_with(self, other_entity: 'EntityInterface') -> bool:
        """Check if this entity can collide with another entity."""
        
        # Check if already collided (for penetration)
        if other_entity.id in self.collision_list:
            return False
        
        # Check penetration limit
        if self.max_penetration_count > 0 and self.current_penetration_count >= self.max_penetration_count:
            return False
        
        return True
    
    def handle_collision(self, other_entity: 'EntityInterface') -> bool:
        """
        Handle collision with another entity.
        Returns True if collision was processed, False otherwise.
        """
        if not self.can_collide_with(other_entity):
            return False
        
        # Add to collision list
        self.collision_list[other_entity.id] = self.collision_cooldown
        self.current_penetration_count += 1
        
        # Apply damage if this entity has damage
        if self.damage > 0 and other_entity:
            killed, actual_damage = other_entity.take_damage(
                factor=1.0,
                element=self.atk_element,
                base_damage=self.damage,
                max_hp_percentage_damage=self.max_hp_percentage_damage,
                current_hp_percentage_damage=self.current_hp_percentage_damage,
                lose_hp_percentage_damage=self.lose_hp_percentage_damage,
                cause_death=self.cause_death,
            )
            print(f"Collision damage: {actual_damage} to {other_entity.__class__.__name__}")
        
        # Apply buffs if this entity has buffs
        if self.buffs and other_entity.buff_component:
            for buff in self.buffs:
                other_entity.buff_component.add_buff(buff)
        
        # Set collision cooldown
        self.collision_cooldown = 0.1  # 100ms cooldown
        
        return True
    
    def check_collision(self, other_entity: 'EntityInterface') -> bool:
        """Check if this entity is colliding with another entity."""
        if not self.entity or not other_entity:
            return False
        
        rect1 = self.entity.get_rect()
        rect2 = other_entity.get_rect()
        
        return rect1.colliderect(rect2)
    
    def get_collision_rect(self) -> pygame.Rect:
        """Get the collision rectangle for this entity."""
        if not self.entity.basic_component:
            return pygame.Rect(0, 0, 0, 0)
        
        return self.entity.basic_component.get_rect()
    
    def set_penetration_count(self, count: int) -> None:
        """Set the maximum penetration count."""
        self.max_penetration_count = count
        self.current_penetration_count = 0
    
    def reset_penetration(self) -> None:
        """Reset penetration count and collision list."""
        self.current_penetration_count = 0
        self.collision_list.clear()
    
    def set_explosion_properties(self, range: float, damage: int, element: str,
                                 max_hp_percentage_damage: int, current_hp_percentage_damage: int,
                                 lose_hp_percentage_damage: int, buffs: List['Buff'] = None) -> None:
        """Set explosion properties."""
        self.explosion_range = range
        self.explosion_damage = damage
        self.explosion_max_hp_percentage_damage = max_hp_percentage_damage
        self.explosion_current_hp_percentage_damage = current_hp_percentage_damage
        self.explosion_lose_hp_percentage_damage = lose_hp_percentage_damage
        self.explosion_element = element
        self.explosion_buffs = buffs or []
    
    def trigger_explosion(self, entities: List['EntityInterface']) -> None:
        """Trigger explosion and damage nearby entities."""
        if self.explosion_range <= 0:
            return
        
        explosion_center = self.entity.get_center()
        
        for entity in entities:
            if not entity.basic_component or not entity.combat_component:
                continue
            
            # Calculate distance
            entity_center = entity.basic_component.get_center()
            distance = math.sqrt(
                (explosion_center[0] - entity_center[0])**2 + 
                (explosion_center[1] - entity_center[1])**2
            )
            
            # Check if within explosion range
            if distance <= self.explosion_range:
                # Apply explosion damage
                killed, actual_damage = entity.take_damage(
                    factor=1.0,
                    element=self.explosion_element,
                    base_damage=self.explosion_damage,
                    max_hp_percentage_damage=self.explosion_max_hp_percentage_damage,
                    current_hp_percentage_damage=self.explosion_current_hp_percentage_damage,
                    lose_hp_percentage_damage=self.explosion_lose_hp_percentage_damage,
                    cause_death=self.cause_death,
                )
                print(f"Explosion damage: {actual_damage} to {entity.__class__.__name__}")
                
                # Apply explosion buffs
                if self.explosion_buffs and entity.buff_component:
                    for buff in self.explosion_buffs:
                        entity.add_buff(buff)
    
    def set_collision_cooldown(self, cooldown: float) -> None:
        """Set collision cooldown time."""
        self.collision_cooldown = cooldown
    
    def get_penetration_remaining(self) -> int:
        """Get remaining penetration count."""
        return max(0, self.max_penetration_count - self.current_penetration_count)
    
    def can_penetrate(self) -> bool:
        """Check if entity can still penetrate."""
        return self.max_penetration_count <= 0 or self.current_penetration_count < self.max_penetration_count
