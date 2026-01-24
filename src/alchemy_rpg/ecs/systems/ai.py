from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Dict, Optional, Any
import math
import random
import pygame

# ECS & Components
import esper
from ..components.common import Position, Velocity, Tag
from ..components.combat import Health, Combat
from ..components.skills import AI
from ..components.interaction import Collider
from ...core.config import TILE_SIZE

# --- Entity Context Facade ---
class EnemyContext:
    """ECS 實體上下文門面，用於在 Action 類中訪問和修改組件。"""
    def __init__(self, world: esper.World, entity_id: int):
        self.world = world
        self.ecs_entity = entity_id
        # Access engine via world if available, assuming world has engine reference
        self.engine = getattr(world, 'engine', None)
        
    def _get_comp(self, component_type):
        return self.world.component_for_entity(self.ecs_entity, component_type)
    
    @property
    def x(self) -> float: return self._get_comp(Position).x
    @property
    def y(self) -> float: return self._get_comp(Position).y
    @property
    def speed(self) -> float: return self._get_comp(Velocity).speed
    
    @property
    def player(self):
        # Helper to find player position - assumes singleton player with 'player' tag
        # In a real engine we might cache this
        for ent, (tag, pos) in self.world.get_components(Tag, Position):
            if tag.tag == "player":
                return pos
        return None

    def set_current_action(self, action_id: str):
        if self.world.has_component(self.ecs_entity, AI):
            self._get_comp(AI).current_action = action_id

    def move(self, dx: float, dy: float, dt: float):
        vel = self._get_comp(Velocity)
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude > 0:
            vel.x = (dx / magnitude) * vel.speed
            vel.y = (dy / magnitude) * vel.speed
        else:
            vel.x = 0
            vel.y = 0

# --- Behavior Tree Nodes ---

class BehaviorNode(ABC):
    @abstractmethod
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        pass

class Sequence(BehaviorNode):
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        for child in self.children:
            if not child.execute(context, dt, current_time):
                return False
        return True

class Selector(BehaviorNode):
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        for child in self.children:
            if child.execute(context, dt, current_time):
                return True
        return False

# --- Actions ---

class Action(ABC):
    def __init__(self, action_id: str, duration: float = 0.0):
        self.action_id = action_id
        self.duration = duration
        self.timer = 0.0
        self.started = False
    
    @abstractmethod
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        pass
    
    @abstractmethod
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        pass
    
    def reset(self) -> None:
        self.timer = 0.0
        self.started = False

class WaitAction(Action):
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)
    
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        self.timer = self.duration
        context.set_current_action(self.action_id)
        # Stop movement
        context.move(0, 0, 0)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        self.timer -= dt
        return self.timer > 0

class ChaseAction(Action):
    def __init__(self, duration: float, action_id: str):
        super().__init__(action_id, duration)
    
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        self.timer = self.duration
        context.set_current_action(self.action_id)
    
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if self.timer <= 0 or not context.player:
            return False
            
        player_pos = context.player
        dx = player_pos.x - context.x
        dy = player_pos.y - context.y
        context.move(dx, dy, dt)
        
        self.timer -= dt
        return True

class PerformNextAction(BehaviorNode):
    def __init__(self, actions: Dict[str, 'Action']):
        self.actions = actions
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        ai_comp = context._get_comp(AI)
        if not ai_comp.action_list:
            return False
        
        action_id = ai_comp.action_list[0]
        action = self.actions.get(action_id)
        
        if not action:
            ai_comp.action_list.pop(0)
            return False
            
        if not action.started:
            action.start(context, current_time)
            action.started = True
            
        if action.update(context, dt, current_time):
            return True # Running
            
        ai_comp.action_list.pop(0)
        action.reset()
        
        return len(ai_comp.action_list) > 0

class AISystem(esper.Processor):
    def process(self, *args, **kwargs):
        dt = args[0] if args else 0.0
        # Assuming current_time is passed or available via engine
        current_time = 0.0 
        
        for ent, (ai, pos) in self.world.get_components(AI, Position):
            if ai.behavior_tree:
                context = EnemyContext(self.world, ent)
                ai.behavior_tree.execute(context, dt, current_time)
