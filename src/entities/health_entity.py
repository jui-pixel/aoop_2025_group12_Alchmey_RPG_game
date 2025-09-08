from typing import *
from basic_entity import BasicEntity
from config import *
import pygame
import math
import random

from src.ulits.elements import WEAKTABLE, ELEMENTS

# Base class for health and defense mechanics
class HealthEntity(BasicEntity):
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 32, 
                 h: int = 32, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "",
                 base_max_hp: int = 100,
                 max_shield: int = 0,
                 dodge_rate: float = 0.0,
                 element: str = "untyped",
                 defense: int = 0,
                 resistances: Optional[Dict[str, float]] = None,
                 invulnerable: bool = False):
        super().__init__(x, y, w, h, image, shape, game, tag)
        
        # Health and Shield
        self._base_max_hp: int = base_max_hp
        self._max_hp: int = base_max_hp
        self._current_hp: int = base_max_hp
        self._max_shield: int = max_shield
        self._current_shield: int = max_shield
        
        # Defense Properties
        self._element: str = element
        self._base_dodge_rate: float = dodge_rate
        self._dodge_rate: float = dodge_rate
        self._base_defense: int = defense
        self._defense = defense
        self._invulnerable: bool = invulnerable
        
        # Elemental Resistances (compatible with buff system)
        if resistances is not None:
            # Ensure all elements are present in resistances
            for elem in ELEMENTS:
                if elem not in resistances:
                    resistances[elem] = 0.0
            self._base_resistances: Dict[str, float] = resistances
        else:
            self._base_resistances: Dict[str, float] = {elem: 0.0 for elem in ELEMENTS}
        
        self._resistances = self._base_resistances.deepcopy()

    # Getters
    @property
    def max_hp(self) -> int:
        return self._max_hp
    
    @property
    def current_hp(self) -> int:
        return self._current_hp
    
    @property
    def base_defense(self) -> int:
        return self._base_defense
    
    @property
    def defense(self) -> int:
        return self._defense
    
    @property
    def max_shield(self) -> int:
        return self._max_shield
    
    @property
    def current_shield(self) -> int:
        return self._current_shield
    
    @property
    def dodge_rate(self) -> float:
        return self._dodge_rate
    
    @property
    def element(self) -> str:
        return self._element
    
    @property
    def invulnerable(self) -> bool:
        return self._invulnerable
    
    @property
    def resistances(self) -> Dict[str, float]:
        return self._resistances

    # Setters
    @defense.setter
    def defense(self, value: int) -> None:
        self._defense = max(0, value)
        
    @defense.setter
    def base_defense(self, value: int) -> None:
        self.set_base_defense(value)
    
    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self.set_max_hp(value)
    
    @current_hp.setter
    def current_hp(self, value: int) -> None:
        self._current_hp = max(0, min(value, self._max_hp))
    
    @max_shield.setter
    def max_shield(self, value: int) -> None:
        self.set_max_shield(value)
    
    @current_shield.setter
    def current_shield(self, value: int) -> None:
        self._current_shield = max(0, min(value, self._max_shield))
    
    @dodge_rate.setter
    def dodge_rate(self, value: float) -> None:
        self._dodge_rate = max(0.0, min(1.0, value))
    
    @element.setter
    def element(self, value: str) -> None:
        if value in ELEMENTS:
            self._element = value
    
    @invulnerable.setter
    def invulnerable(self, value: bool) -> None:
        self._invulnerable = value

    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                   max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                   lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        if self.invulnerable:
            return False, 0
            
        if self.dodge_rate > 0:
            if random.random() < self.dodge_rate:
                return False, 0
        
        affinity_multiplier = self._calculate_affinity_multiplier(element)
        
        if max_hp_percentage_damage > 0:
            base_damage += self.max_hp * max_hp_percentage_damage / 100
        if current_hp_percentage_damage > 0:
            base_damage += self.current_hp * current_hp_percentage_damage / 100
        if lose_hp_percentage_damage > 0:
            base_damage += (self.max_hp - self.current_hp) * lose_hp_percentage_damage / 100
        
        resistance = self.resistances.get(element, 0.0)
        final_damage = max(1, int(base_damage * affinity_multiplier * (1.0 - resistance) * factor - self.defense))
        
        if self.current_shield > 0:
            shield_damage = min(final_damage, self.current_shield)
            self.current_shield -= shield_damage
            final_damage -= shield_damage
        
        if final_damage > 0:
            remain_hp = self.current_hp - final_damage
            if remain_hp <= 0 and not cause_death:
                final_damage = self.current_hp - 1
                self.current_hp = 1
            else:
                self.current_hp = remain_hp
        
        killed = self.current_hp <= 0
        if killed:
            self.current_hp = 0
        
        return killed, final_damage
    
    def _calculate_affinity_multiplier(self, element: str) -> float:
        if element == 'untyped' or self.element == 'untyped':
            return 1.0
        
        # Check WEAKTABLE for direct weakness
        for attacker, defender in WEAKTABLE:
            if (element == attacker and self.element == defender):
                return 1.5  # Weakness: attacker deals more damage
            elif (element == defender and self.element == attacker):
                return 0.5  # Resistance: defender takes less damage
        
        # Fallback to neutral if no direct match
        return 1.0
    
    def heal(self, amount: int) -> None:
        self.current_hp = min(self.max_hp, self.current_hp + amount)
    
    def add_shield(self, amount: int) -> None:
        self.current_shield = min(self.max_shield, self.current_shield + amount)
    
    def set_max_hp(self, new_max_hp: int) -> None:
        old_max = self.max_hp
        self._max_hp = max(0, new_max_hp)
        if old_max > 0:
            self.current_hp = int(self.current_hp * new_max_hp / old_max)
    
    def set_max_shield(self, new_max_shield: int) -> None:
        self._max_shield = max(0, new_max_shield)
        self.current_shield = min(self.max_shield, self.current_shield)
    
    def set_resistance(self, element: str, resistance: float) -> None:
        if element in ELEMENTS:
            self.resistances[element] = max(0.0, min(1.0, resistance))
    
    def get_health_percentage(self) -> float:
        if self.max_hp <= 0:
            return 0.0
        return self.current_hp / self.max_hp
    
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def set_base_defense(self, value: int) -> None:
        self._base_defense = max(0, value)
        self._defense = self._base_defense  # Reset defense to base when updating base_defense


# Example: Enemy class that inherits from all three (multiple inheritance)
# class Enemy(HealthEntity, MovementEntity, AttackEntity):
#     def __init__(self, 
#                  x: float = 0.0, 
#                  y: float = 0.0, 
#                  w: int = 32, 
#                  h: int = 32, 
#                  image: Optional[pygame.Surface] = None, 
#                  shape: str = "rect", 
#                  game: 'Game' = None, 
#                  tag: str = "enemy",
#                  base_max_hp: int = 100,
#                  max_shield: int = 0,
#                  dodge_rate: float = 0.0,
#                  max_speed: float = 100.0,
#                  element: str = "untyped",
#                  resistances: Optional[Dict[str, float]] = None,
#                  damage_to_element: Optional[Dict[str, float]] = None,
#                  can_move: bool = True,
#                  can_attack: bool = True,
#                  invulnerable: bool = False):
#         # Initialize in order to handle multiple inheritance properly
#         # HealthEntity init first for health props
#         HealthEntity.__init__(self, x, y, w, h, image, shape, game, tag, base_max_hp, max_shield, dodge_rate, element, resistances, invulnerable)
#         # MovementEntity init next
#         MovementEntity.__init__(self, x, y, w, h, image, shape, game, tag, max_speed, can_move)
#         # AttackEntity init last
#         AttackEntity.__init__(self, x, y, w, h, image, shape, game, tag, can_attack, damage_to_element)
        
#         # Override any conflicting properties if needed (e.g., ensure consistent values)

# # Example: Bullet class that inherits from MovementEntity and AttackEntity (no health)
# class Bullet(MovementEntity, AttackEntity):
#     def __init__(self, 
#                  x: float = 0.0, 
#                  y: float = 0.0, 
#                  w: int = 8, 
#                  h: int = 8, 
#                  image: Optional[pygame.Surface] = None, 
#                  shape: str = "rect", 
#                  game: 'Game' = None, 
#                  tag: str = "bullet",
#                  max_speed: float = 200.0,
#                  can_move: bool = True,
#                  can_attack: bool = True,
#                  damage_to_element: Optional[Dict[str, float]] = None,
#                  element: str = "untyped"):  # Bullet might have an element for damage type
#         # Initialize MovementEntity first
#         MovementEntity.__init__(self, x, y, w, h, image, shape, game, tag, max_speed, can_move)
#         # Then AttackEntity
#         AttackEntity.__init__(self, x, y, w, h, image, shape, game, tag, can_attack, damage_to_element)
        
#         # Bullets don't have health, but if needed, could add a simple health prop or ignore collisions for damage intake
#         # For attack, override perform_attack to apply damage on collision without needing health

#     # Override perform_attack for bullet-specific logic, e.g., destroy on hit
#     def perform_attack(self, target: 'HealthEntity', base_damage: int, element: str = "untyped") -> bool:
#         if not self.can_attack:
#             return False
        
#         multiplier = self.damage_to_element.get(element, 1.0)
#         effective_damage = int(base_damage * multiplier)
        
#         killed, actual_damage = target.take_damage(base_damage=effective_damage, element=element)
        
#         # Bullet destroys itself after attack (assuming collision triggers this)
#         if killed or actual_damage > 0:
#             self.destroy()  # Assume a destroy method exists in BasicEntity or add one
        
#         return killed