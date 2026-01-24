import esper
import pygame
import math
import random
from typing import List, Dict, Optional, TYPE_CHECKING
from ..core.config import TILE_SIZE
from .components import (
    Position, Velocity, Renderable, Collider, Health, Defense, Combat, Buffs, AI, Tag,
    NPCInteractComponent, DungeonPortalComponent, PlayerComponent, TreasureStateComponent,
    TimerComponent
)

# Imports for AI classes - assuming they will be in systems.ai
# from .systems.ai import (
#     ChaseAction, AttackAction, WaitAction, PatrolAction, DodgeAction, 
#     SpecialAttackAction, MeleeAttackAction, RandomMoveAction, 
#     RefillActionList, PerformNextAction, Sequence, Selector, 
#     StrafeAction, DashAction, DashBackAction, FanAttackAction, RadialBurstAction, TauntAction,
#     EnemyContext
# )

if TYPE_CHECKING:
    from ..core.engine import Engine

def create_player_entity(world: esper.World, x: float = 0.0, y: float = 0.0, tag: str = "player", engine: 'Engine' = None) -> int:
    player = world.create_entity()
    world.add_component(player, Tag(tag=tag))
    world.add_component(player, Position(x=x, y=y))
    world.add_component(player, Renderable(color=(0, 0, 255), layer=1, w=TILE_SIZE, h=TILE_SIZE))
    world.add_component(player, Collider(w=TILE_SIZE, h=TILE_SIZE, collision_group="player"))
    world.add_component(player, Health(max_hp=100, current_hp=100, max_shield=5))
    world.add_component(player, Defense(defense=5, dodge_rate=0.05))
    world.add_component(player, Combat(damage=10, collision_cooldown=0.5))
    world.add_component(player, Buffs())
    world.add_component(player, PlayerComponent(energy=100, max_energy=100))
    world.add_component(player, Velocity(speed=4*TILE_SIZE))
    return player

def create_dummy_entity(world: esper.World, x: float, y: float) -> int:
    ent = world.create_entity()
    world.add_component(ent, Position(x=x, y=y))
    world.add_component(ent, Renderable(color=(200, 200, 200), w=32, h=32))
    world.add_component(ent, Collider(w=32, h=32, collision_group="npc"))
    world.add_component(ent, Health(max_hp=9999, current_hp=9999))
    world.add_component(ent, Tag(tag="dummy"))
    return ent

def create_damage_text_entity(world: esper.World, x: float, y: float, damage: int, color=(255,0,0), duration: float=1.0):
    ent = world.create_entity()
    world.add_component(ent, Position(x=x, y=y))
    world.add_component(ent, Velocity(x=0, y=-30))
    
    font = pygame.font.SysFont('Arial', 24)
    surf = font.render(str(damage), True, color)
    world.add_component(ent, Renderable(image=surf, shape="text", w=surf.get_width(), h=surf.get_height(), layer=2))
    
    world.add_component(ent, TimerComponent(duration=duration, on_expire=lambda: world.delete_entity(ent)))
    return ent

# Placeholder for other create functions (Enemy, Boss, NPCs) 
# I will implement them fully when I have the AI classes ready.
