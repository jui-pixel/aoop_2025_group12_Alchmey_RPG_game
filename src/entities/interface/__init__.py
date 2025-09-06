"""
Entity Interface System
This module provides a comprehensive interface system for game entities based on the draw.io diagram.
"""

from .entity_interface import EntityInterface, ComponentInterface
from .basic_component import BasicComponent
from .combat_component import CombatComponent
from .movement_component import MovementComponent
from .buff_component import BuffComponent, BuffSynthesizer
from .collision_component import CollisionComponent
from .behavior_component import BehaviorComponent, BehaviorState
from .behavior_tree import (BehaviorTreeComponent, Action, ChaseAction, AttackAction, 
                          WaitAction, BehaviorNode, Selector, Sequence, ConditionNode,
                          PerformNextAction, RefillActionList, IdleNode)
from .timing_component import TimingComponent
from .damage_calculator import DamageCalculator

__all__ = [
    'EntityInterface',
    'ComponentInterface',
    'BasicComponent',
    'CombatComponent',
    'MovementComponent',
    'BuffComponent',
    'BuffSynthesizer',
    'CollisionComponent',
    'BehaviorComponent',
    'BehaviorState',
    'BehaviorTreeComponent',
    'Action',
    'ChaseAction',
    'AttackAction',
    'WaitAction',
    'BehaviorNode',
    'Selector',
    'Sequence',
    'ConditionNode',
    'PerformNextAction',
    'RefillActionList',
    'IdleNode',
    'TimingComponent',
    'DamageCalculator'
]
