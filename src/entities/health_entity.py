from typing import *
from basic_entity import BasicEntity
from config import *
import pygame
import math
import random

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
        self._invulnerable: bool = invulnerable
        
        # Elemental Resistances
        self._resistances: Dict[str, float] = resistances if resistances is not None else {
            'untyped': 0.0, 'light': 0.0, 'dark': 0.0, 'metal': 0.0, 'wood': 0.0,
            'water': 0.0, 'fire': 0.0, 'earth': 0.0, 'ice': 0.0, 'electric': 0.0, 'wind': 0.0
        }

    # Getters
    @property
    def max_hp(self) -> int:
        return self._max_hp
    
    @property
    def current_hp(self) -> int:
        return self._current_hp
    
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
        if value in self._resistances:
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
        final_damage = max(1, int(base_damage * affinity_multiplier * (1.0 - resistance) * factor))
        
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
        
        if (element == 'light' and self.element == 'dark') or \
           (element == 'dark' and self.element == 'light'):
            return 1.5
        
        cycle = ['metal', 'wood', 'earth', 'water', 'fire']
        if element in cycle and self.element in cycle:
            element_idx = cycle.index(element)
            self_idx = cycle.index(self.element)
            if (element_idx + 1) % len(cycle) == self_idx:
                return 1.5
        
        special_affinities = [
            ('earth', 'electric'),
            ('wood', 'wind'),
            ('fire', 'ice')
        ]
        
        for elem1, elem2 in special_affinities:
            if (element == elem1 and self.element == elem2) or \
               (element == elem2 and self.element == elem1):
                return 1.5
        
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
        if element in self.resistances:
            self.resistances[element] = max(0.0, min(1.0, resistance))
    
    def get_health_percentage(self) -> float:
        if self.max_hp <= 0:
            return 0.0
        return self.current_hp / self.max_hp
    
    def is_alive(self) -> bool:
        return self.current_hp > 0

# Base class for movement mechanics
class MovementEntity(BasicEntity):
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 32, 
                 h: int = 32, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "",
                 max_speed: float = 100.0,
                 can_move: bool = True):
        super().__init__(x, y, w, h, image, shape, game, tag)
        
        # Movement
        self._base_max_speed: float = max_speed
        self._max_speed: float = max_speed
        self._speed: float = max_speed
        self._velocity: Tuple[float, float] = (0.0, 0.0)
        self._displacement: Tuple[float, float] = (0.0, 0.0)
        
        self._can_move: bool = can_move

    # Getters
    @property
    def max_speed(self) -> float:
        return self._max_speed
    
    @property
    def speed(self) -> float:
        return self._speed
    
    @property
    def velocity(self) -> Tuple[float, float]:
        return self._velocity
    
    @property
    def displacement(self) -> Tuple[float, float]:
        return self._displacement
    
    @property
    def can_move(self) -> bool:
        return self._can_move

    # Setters
    @max_speed.setter
    def max_speed(self, value: float) -> None:
        self._max_speed = max(0.0, value)
        self._speed = self._max_speed
    
    @speed.setter
    def speed(self, value: float) -> None:
        self._speed = max(0.0, min(value, self._max_speed))
    
    @velocity.setter
    def velocity(self, value: Tuple[float, float]) -> None:
        self._velocity = value
    
    @displacement.setter
    def displacement(self, value: Tuple[float, float]) -> None:
        self._displacement = value
    
    @can_move.setter
    def can_move(self, value: bool) -> None:
        self._can_move = value

    def move(self, dx: float, dy: float, dt: float) -> None:
        if not self.can_move:
            self.velocity = (0.0, 0.0)
            self.displacement = (0.0, 0.0)
            return

        # Calculate input magnitude
        length = math.sqrt(dx**2 + dy**2)
        
        if length > 0:
            # Full speed in input direction
            dx, dy = dx / length, dy / length
            self.displacement = (dx, dy)
            self.velocity = (dx * self.max_speed, dy * self.max_speed)
        else:
            # Lerp velocity towards zero
            lerp_factor = 0.1
            vx = self.velocity[0] * (1 - lerp_factor)
            vy = self.velocity[1] * (1 - lerp_factor)
            self.velocity = (vx, vy)
            self.displacement = (0.0, 0.0)
            
            # Stop if velocity is very low
            if math.sqrt(vx**2 + vy**2) < self.max_speed * 0.05:
                self.velocity = (0.0, 0.0)

        # Update position
        new_x = self.x + self.velocity[0] * dt
        new_y = self.y + self.velocity[1] * dt
        
        if not self.pass_wall:
            tile_x, tile_y = int(new_x // TILE_SIZE), int(new_y // TILE_SIZE)
            
            # Check if new position is valid
            x_valid = 0 <= tile_x < self.dungeon.grid_width
            y_valid = 0 <= tile_y < self.dungeon.grid_height
            
            if x_valid and y_valid:
                tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile in PASSABLE_TILES:
                    self.set_position(new_x, new_y)
                else:
                    # Try sliding along X or Y axis
                    x_allowed = x_valid and self.dungeon.dungeon_tiles[int(self.y // TILE_SIZE)][tile_x] in PASSABLE_TILES
                    y_allowed = y_valid and self.dungeon.dungeon_tiles[tile_y][int(self.x // TILE_SIZE)] in PASSABLE_TILES
                    
                    if x_allowed:
                        self.set_position(new_x, self.y)
                        self.velocity = (self.velocity[0], 0.0)
                    if y_allowed:
                        self.set_position(self.x, new_y)
                        self.velocity = (0.0, self.velocity[1])
                    if not (x_allowed or y_allowed):
                        self.velocity = (0.0, 0.0)
        else:
            self.set_position(new_x, new_y)

# Base class for attack and collision mechanics
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
                 damage_to_element: Optional[Dict[str, float]] = None):
        super().__init__(x, y, w, h, image, shape, game, tag)
        
        # Attack Properties
        self._can_attack: bool = can_attack
        
        # Damage Multipliers (for output damage)
        self._damage_to_element: Dict[str, float] = damage_to_element if damage_to_element is not None else {
            'untyped': 1.0, 'light': 1.0, 'dark': 1.0, 'metal': 1.0, 'wood': 1.0,
            'water': 1.0, 'fire': 1.0, 'earth': 1.0, 'ice': 1.0, 'electric': 1.0, 'wind': 1.0
        }

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
        self._can_attack = value

    # Placeholder for attack logic (e.g., collision-based attack)
    # This would typically be overridden in subclasses to handle collision detection and damage application
    def perform_attack(self, target: 'CombatEntity', base_damage: int, element: str = "untyped") -> bool:
        if not self.can_attack:
            return False
        
        # Example: Apply damage based on collision (assuming collision is checked externally)
        # In a full implementation, this would integrate with collision detection
        multiplier = self.damage_to_element.get(element, 1.0)
        effective_damage = int(base_damage * multiplier)
        
        # Assuming target has take_damage method (from HealthEntity)
        killed, actual_damage = target.take_damage(base_damage=effective_damage, element=element)
        return killed

    def set_damage_multiplier(self, element: str, multiplier: float) -> None:
        if element in self.damage_to_element:
            self.damage_to_element[element] = max(0.0, multiplier)

# Example: Enemy class that inherits from all three (multiple inheritance)
class Enemy(HealthEntity, MovementEntity, AttackEntity):
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 32, 
                 h: int = 32, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "enemy",
                 base_max_hp: int = 100,
                 max_shield: int = 0,
                 dodge_rate: float = 0.0,
                 max_speed: float = 100.0,
                 element: str = "untyped",
                 resistances: Optional[Dict[str, float]] = None,
                 damage_to_element: Optional[Dict[str, float]] = None,
                 can_move: bool = True,
                 can_attack: bool = True,
                 invulnerable: bool = False):
        # Initialize in order to handle multiple inheritance properly
        # HealthEntity init first for health props
        HealthEntity.__init__(self, x, y, w, h, image, shape, game, tag, base_max_hp, max_shield, dodge_rate, element, resistances, invulnerable)
        # MovementEntity init next
        MovementEntity.__init__(self, x, y, w, h, image, shape, game, tag, max_speed, can_move)
        # AttackEntity init last
        AttackEntity.__init__(self, x, y, w, h, image, shape, game, tag, can_attack, damage_to_element)
        
        # Override any conflicting properties if needed (e.g., ensure consistent values)

# Example: Bullet class that inherits from MovementEntity and AttackEntity (no health)
class Bullet(MovementEntity, AttackEntity):
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 8, 
                 h: int = 8, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "bullet",
                 max_speed: float = 200.0,
                 can_move: bool = True,
                 can_attack: bool = True,
                 damage_to_element: Optional[Dict[str, float]] = None,
                 element: str = "untyped"):  # Bullet might have an element for damage type
        # Initialize MovementEntity first
        MovementEntity.__init__(self, x, y, w, h, image, shape, game, tag, max_speed, can_move)
        # Then AttackEntity
        AttackEntity.__init__(self, x, y, w, h, image, shape, game, tag, can_attack, damage_to_element)
        
        # Bullets don't have health, but if needed, could add a simple health prop or ignore collisions for damage intake
        # For attack, override perform_attack to apply damage on collision without needing health

    # Override perform_attack for bullet-specific logic, e.g., destroy on hit
    def perform_attack(self, target: 'HealthEntity', base_damage: int, element: str = "untyped") -> bool:
        if not self.can_attack:
            return False
        
        multiplier = self.damage_to_element.get(element, 1.0)
        effective_damage = int(base_damage * multiplier)
        
        killed, actual_damage = target.take_damage(base_damage=effective_damage, element=element)
        
        # Bullet destroys itself after attack (assuming collision triggers this)
        if killed or actual_damage > 0:
            self.destroy()  # Assume a destroy method exists in BasicEntity or add one
        
        return killed