# src.ecs_factory.py

# src.ecs_factory.py

import esper
import pygame
import math
from typing import List, Dict, Optional, TYPE_CHECKING
# 類型檢查：假設 Game 類在 src.game 模組中
if TYPE_CHECKING:
    from src.game import Game 

# 假設 TILE_SIZE 在 src.config 模組中
from src.config import TILE_SIZE 

# 假設這些是您自定義的組件 (Components)
from ..ecs.components import (
    Position, Velocity, Renderable, Collider, Health, Defense, Combat, Buffs, AI, Tag, 
    NPCInteractComponent, DungeonPortalComponent
)

# 假設這些是您自定義的 AI 行為和行為樹節點
from ..ecs.ai import (
    EnemyContext,
    ChaseAction, AttackAction, WaitAction, PatrolAction, DodgeAction, 
    SpecialAttackAction, MeleeAttackAction, RandomMoveAction, # 動作類
    RefillActionList, PerformNextAction, Sequence, Selector, ConditionNode, PlaceholderAction # 行為樹節點
)

def create_enemy1_entity(
    world: esper.World, x: float = 0.0, y: float = 0.0, game: 'Game' = None, tag: str = "enemy",
    base_max_hp: int = 100, max_speed: float = 2 * TILE_SIZE, element: str = "fire", 
    defense: int = 10, damage: int = 5, w: int = TILE_SIZE // 2, h: int = TILE_SIZE // 2
) -> int:
    """
    創建一個 Enemy1 ECS 實體並附上所有組件。
    """
    # 1. 創建實體
    enemy = world.create_entity()

    # 2. 初始化動作和行為樹
    patrol_points = [(x + i * TILE_SIZE * 2, y) for i in range(-2, 3)]
    
    actions = {
        'chase': ChaseAction(duration=0.3, action_id='chase', direction_source=lambda e: (
            (e.player.x - e.x) / max(1e-10, math.hypot(e.player.x - e.x, e.player.y - e.y)),
            (e.player.y - e.y) / max(1e-10, math.hypot(e.player.x - e.x, e.player.y - e.y))
        )),
        'chase2': ChaseAction(duration=0.5, action_id='chase2', direction_source=lambda e: (
            (e.player.x - e.x) / max(1e-10, math.hypot(e.player.x - e.x, e.player.y - e.y)),
            (e.player.y - e.y) / max(1e-10, math.hypot(e.player.x - e.x, e.player.y - e.y))
        )),
        'attack': AttackAction(action_id='attack', damage=damage, tag=tag),
        'pause': WaitAction(duration=0.3, action_id='pause'),
        'pause2': WaitAction(duration=1.0, action_id='pause2'),
        'pause3': WaitAction(duration=0.5, action_id='pause3'),
        'patrol': PatrolAction(duration=5.0, action_id='patrol', waypoints=patrol_points),
        'dodge': DodgeAction(duration=0.3, action_id='dodge'),
        'special_attack': SpecialAttackAction(action_id='special_attack', damage=damage * 2, tag=tag),
        'melee': MeleeAttackAction(action_id='melee', damage=50),
        'random_move': RandomMoveAction(duration=0.5, action_id='random_move', speed=max_speed),
    }

    # 行為樹邏輯 (保持原樣，但使用 EnemyContext)
    def get_default_combo(context: EnemyContext) -> List[str]:
        if not context.player:
            return ['patrol', 'pause']
        hp_ratio = context.current_hp / context.max_hp
        distance = math.hypot(context.player.x - context.x, context.player.y - context.y)
        
        # Check for nearby player bullets
        bullet_nearby = False
        for bullet in context.game.entity_manager.bullet_group:
            if bullet.tag != "player": continue
            if math.hypot(bullet.x - context.x, bullet.y - context.y) < 3 * TILE_SIZE:
                bullet_nearby = True
                break
        
        ai_comp = context._get_comp(AI)
        if hp_ratio < 0.5 and not ai_comp.half_hp_triggered:
            ai_comp.half_hp_triggered = True
            return ['special_attack'] * 10
        elif bullet_nearby:
            return ['dodge', 'pause', 'attack', 'pause']
        elif distance < 3 * TILE_SIZE:
            return ['chase2', 'melee', 'pause', 'random_move']
        elif distance < context.vision_radius * TILE_SIZE:
            return ['attack', 'dodge', 'attack', 'chase', 'random_move']
        else:
            return ['patrol', 'pause']

    refill_node = RefillActionList(actions, get_default_combo)
    
    # 執行動作列表，並在列表為空時重新填充
    perform_action_sequence = Sequence([
        PerformNextAction(actions),
        refill_node,
    ])
    
    # 根節點
    behavior_tree = Selector([
        # Emergency check: if not alive, should be removed by HealthSystem
        # ConditionNode(lambda e, t: not e.is_alive(), PlaceholderAction(action_id='die'), # Assuming PlaceholderAction exists
        # Main combat/patrol loop
        perform_action_sequence
    ])
    
    # 3. 附加組件
    
    # 幾何與運動
    world.add_component(enemy, Position(x=x, y=y))
    world.add_component(enemy, Velocity(speed=max_speed, x=0.0, y=0.0))
    world.add_component(enemy, Collider(w=w, h=h, tag=tag))
    
    # 健康與戰鬥
    world.add_component(enemy, Health(max_hp=base_max_hp, current_hp=base_max_hp, defense=defense, dodge_rate=0.0))
    world.add_component(enemy, Combat(damage=damage, atk_element=element, tag=tag, collision_cooldown=0.1))
    
    # 渲染
    image = pygame.Surface((w, h))
    image.fill((0, 255, 0)) # 綠色方塊
    world.add_component(enemy, Renderable(image=image, layer=1, w=w, h=h))
    
    # AI
    world.add_component(enemy, AI(
        behavior_tree=behavior_tree,
        action_list=[],
        actions=actions,
        vision_radius=15,
    ))

    return enemy


def create_alchemy_pot_npc(
    world: esper,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 64, 
    h: int = 64, 
    tag: str = "alchemy_pot_npc",
    base_max_hp: int = 999999, 
    element: str = "earth", 
    defense: int = 100,
    invulnerable: bool = True
) -> int:
    """創建一個 ECS 煉金鍋 NPC 實體。"""
    
    npc_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(npc_entity, Tag(tag=tag))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    # 注意：這裡應該載入圖片，但為了簡化，我們只設定屬性
    world.add_component(npc_entity, Renderable(
        image=None, 
        shape="rect",
        w=w,
        h=h,
        color=(139, 69, 19), # 棕色
        layer=0 
    ))

    # 3. 碰撞器 (用於交互距離檢查)
    world.add_component(npc_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=False, 
        collision_group="npc"
    ))

    # 4. 健康與防禦
    world.add_component(npc_entity, Health(
        max_hp=base_max_hp,
        current_hp=base_max_hp,
        max_shield=0,
        current_shield=0
    ))
    world.add_component(npc_entity, Defense(
        defense=defense,
        dodge_rate=0.0,
        element=element,
        resistances=None,
        invulnerable=invulnerable
    ))

    # 5. 增益效果 (Buffs)
    world.add_component(npc_entity, Buffs())

    # 6. 煉金鍋專屬狀態
    world.add_component(npc_entity, NPCInteractComponent()) 

    return npc_entity

def create_dummy_entity(
    world: esper,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 32, 
    h: int = 32,
    base_max_hp: int = 999999999 # 模擬無限生命
) -> int:
    """創建一個 ECS 訓練假人實體。"""
    
    dummy_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(dummy_entity, Tag(tag="dummy"))
    world.add_component(dummy_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    # (註：這裡應處理圖片載入，但在 ECS 中我們只設定屬性)
    world.add_component(dummy_entity, Renderable(
        image=None,
        shape="rect",
        w=w,
        h=h,
        color=(255, 0, 0), # 紅色
        layer=1 # 可能比地圖高
    ))

    # 3. 碰撞器 (假人是靜止的)
    world.add_component(dummy_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=False, 
        collision_group="enemy_dummy" # 假設有一個專門的碰撞組
    ))

    # 4. 健康與防禦
    world.add_component(dummy_entity, Health(
        max_hp=base_max_hp,
        current_hp=base_max_hp,
        regen_rate=base_max_hp
    ))
    world.add_component(dummy_entity, Defense(
        defense=0,
        element="untyped",
        invulnerable=False # 允許受到傷害
    ))


    return dummy_entity

def create_dungeon_portal_npc(
    world: esper,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 64, 
    h: int = 64, 
    available_dungeons: Optional[List[Dict]] = None
) -> int:
    """創建一個 ECS 地牢傳送門 NPC 實體。"""
    
    npc_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(npc_entity, Tag(tag="dungeon_portal_npc"))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    world.add_component(npc_entity, Renderable(
        image=None,
        shape="rect",
        w=w,
        h=h,
        color=(128, 0, 128), # 紫色
        layer=0 
    ))

    # 3. 碰撞器
    world.add_component(npc_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=False, 
        collision_group="portal"
    ))

    # 4. 健康與防禦 (高防禦且無敵)
    world.add_component(npc_entity, Health(max_hp=999999, current_hp=999999))
    world.add_component(npc_entity, Defense(
        defense=100,
        element="untyped",
        invulnerable=True
    ))

    # 5. 增益效果
    world.add_component(npc_entity, Buffs())

    # 6. NPC 交互狀態 (interaction_range=80.0)
    world.add_component(npc_entity, NPCInteractComponent(interaction_range=80.0))
    
    # 7. 傳送門專屬狀態
    world.add_component(npc_entity, DungeonPortalComponent(
        available_dungeons=available_dungeons or [{'name': 'Test Dungeon', 'level': 1, 'dungeon_id': 1}]
    ))

    return npc_entity

def create_magic_crystal_npc(
    world: esper,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 64, 
    h: int = 64, 
    tag: str = "magic_crystal_npc",
    base_max_hp: int = 999999, 
    element: str = "light", 
    defense: int = 100,
    invulnerable: bool = True
) -> int:
    """創建一個 ECS 魔法水晶 NPC 實體。"""
    
    npc_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(npc_entity, Tag(tag=tag))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    world.add_component(npc_entity, Renderable(
        image=None, # 讓 RenderSystem 處理載入白色水晶圖像
        shape="rect",
        w=w,
        h=h,
        color=(255, 255, 255), # 白色
        layer=0 
    ))

    # 3. 碰撞器
    world.add_component(npc_entity, Collider(
        w=w, 
        h=h, 
        pass_wall=False, 
        collision_group="npc"
    ))

    # 4. 健康與防禦
    world.add_component(npc_entity, Health(
        max_hp=base_max_hp,
        current_hp=base_max_hp
    ))
    world.add_component(npc_entity, Defense(
        defense=defense,
        element=element,
        invulnerable=invulnerable
    ))

    # 5. 增益效果 (Buffs)
    world.add_component(npc_entity, Buffs())

    # 6. NPC 交互狀態 (interaction_range=80.0, is_interacting=False)
    world.add_component(npc_entity, NPCInteractComponent(interaction_range=80.0)) 

    return npc_entity