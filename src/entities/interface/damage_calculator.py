"""
Damage Calculator Utility
Handles damage calculation logic based on the draw.io diagram specifications.
"""

from typing import Tuple, Optional
from .entity_interface import EntityInterface


class DamageCalculator:
    """
    Damage calculator that implements the damage calculation logic from the draw.io diagram:
    1. Check for dodge (combat attributes -> dodge rate%)
    2. Calculate damage = original_damage * (elemental_affinity?) * elemental_resistance
    3. If shield exists, deduct from shield first
    4. If shield <= 0, remaining damage is lost
    5. If no shield, apply damage directly to HP
    """
    
    @staticmethod
    def calculate_damage(attacker: EntityInterface, target: EntityInterface, 
                        base_damage: int, element: str) -> Tuple[bool, int]:
        """
        Calculate damage dealt from attacker to target.
        
        Args:
            attacker: The entity dealing damage
            target: The entity receiving damage
            base_damage: Base damage amount
            element: Element type of the damage
            
        Returns:
            Tuple of (killed, actual_damage)
        """
        if not target.combat_component:
            return False, 0
        
        # 1. Check for dodge
        if target.combat_component.dodge_rate > 0:
            import random
            if random.random() < target.combat_component.dodge_rate:
                print(f"Attack dodged by {target.__class__.__name__}")
                return False, 0
        
        # 2. Calculate elemental affinity multiplier
        affinity_multiplier = DamageCalculator._calculate_affinity_multiplier(
            element, target.combat_component.element
        )
        
        # 3. Apply elemental resistance
        resistance = target.combat_component.resistances.get(element, 0.0)
        final_damage = max(1, int(base_damage * affinity_multiplier * (1.0 - resistance)))
        
        print(f"Damage calculation: {base_damage} -> {final_damage} "
              f"(affinity: {affinity_multiplier:.2f}, resistance: {resistance:.2f})")
        
        # 4. Apply damage to shield first
        if target.combat_component.current_shield > 0:
            shield_damage = min(final_damage, target.combat_component.current_shield)
            target.combat_component.current_shield -= shield_damage
            final_damage -= shield_damage
            
            print(f"Shield absorbed {shield_damage} damage, remaining shield: {target.combat_component.current_shield}")
            
            # 5. If shield is depleted, remaining damage is lost
            if target.combat_component.current_shield <= 0:
                final_damage = 0
                print("Shield depleted, remaining damage lost")
        
        # 6. Apply remaining damage to HP
        if final_damage > 0:
            target.combat_component.current_hp -= final_damage
            print(f"Applied {final_damage} damage to HP, remaining HP: {target.combat_component.current_hp}")
        
        # Check if target is killed
        killed = target.combat_component.current_hp <= 0
        if killed:
            target.combat_component.current_hp = 0
            print(f"{target.__class__.__name__} killed!")
        
        return killed, base_damage  # Return original damage for display purposes
    
    @staticmethod
    def _calculate_affinity_multiplier(attack_element: str, target_element: str) -> float:
        """
        Calculate elemental affinity multiplier based on the draw.io diagram.
        
        Args:
            attack_element: Element of the attack
            target_element: Element of the target
            
        Returns:
            Affinity multiplier (1.0 = normal, 1.5 = effective)
        """
        if attack_element == 'untyped' or target_element == 'untyped':
            return 1.0
        
        # Light vs Dark
        if (attack_element == 'light' and target_element == 'dark') or \
           (attack_element == 'dark' and target_element == 'light'):
            return 1.5
        
        # Elemental cycle: Metal > Wood > Earth > Water > Fire > Metal
        cycle = ['metal', 'wood', 'earth', 'water', 'fire']
        if attack_element in cycle and target_element in cycle:
            attack_idx = cycle.index(attack_element)
            target_idx = cycle.index(target_element)
            if (attack_idx + 1) % len(cycle) == target_idx:
                return 1.5
        
        # Special affinities
        special_affinities = [
            ('earth', 'electric'),
            ('wood', 'wind'),
            ('fire', 'ice')
        ]
        
        for elem1, elem2 in special_affinities:
            if (attack_element == elem1 and target_element == elem2) or \
               (attack_element == elem2 and target_element == elem1):
                return 1.5
        
        return 1.0
    
    @staticmethod
    def calculate_collision_damage(collision_entity: EntityInterface, 
                                 target: EntityInterface) -> Tuple[bool, int]:
        """
        Calculate damage from collision between entities.
        
        Args:
            collision_entity: Entity causing collision damage
            target: Entity receiving collision damage
            
        Returns:
            Tuple of (killed, actual_damage)
        """
        if not collision_entity.collision_component:
            return False, 0
        
        damage = collision_entity.collision_component.damage
        element = collision_entity.collision_component.element
        
        return DamageCalculator.calculate_damage(collision_entity, target, damage, element)
    
    @staticmethod
    def calculate_explosion_damage(explosion_center: Tuple[float, float],
                                 explosion_range: float, explosion_damage: int,
                                 explosion_element: str, target: EntityInterface) -> Tuple[bool, int]:
        """
        Calculate damage from explosion.
        
        Args:
            explosion_center: Center position of explosion
            explosion_range: Range of explosion
            explosion_damage: Base explosion damage
            explosion_element: Element of explosion
            target: Target entity
            
        Returns:
            Tuple of (killed, actual_damage)
        """
        if not target.basic_component:
            return False, 0
        
        # Calculate distance to explosion center
        target_pos = target.basic_component.get_center()
        distance = ((explosion_center[0] - target_pos[0])**2 + 
                   (explosion_center[1] - target_pos[1])**2)**0.5
        
        # Check if within explosion range
        if distance > explosion_range:
            return False, 0
        
        # Calculate damage (could be reduced by distance)
        damage_multiplier = 1.0 - (distance / explosion_range) * 0.5  # 50% damage reduction at edge
        final_damage = int(explosion_damage * damage_multiplier)
        
        return DamageCalculator.calculate_damage(None, target, final_damage, explosion_element)
    
    @staticmethod
    def get_effective_damage(base_damage: int, element: str, 
                           target_resistances: dict, target_element: str) -> int:
        """
        Calculate effective damage without applying it.
        
        Args:
            base_damage: Base damage amount
            element: Element type
            target_resistances: Target's resistance values
            target_element: Target's element
            
        Returns:
            Effective damage amount
        """
        # Calculate affinity
        affinity_multiplier = DamageCalculator._calculate_affinity_multiplier(element, target_element)
        
        # Apply resistance
        resistance = target_resistances.get(element, 0.0)
        effective_damage = max(1, int(base_damage * affinity_multiplier * (1.0 - resistance)))
        
        return effective_damage
