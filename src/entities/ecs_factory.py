# src.ecs_factory.py

# src.ecs_factory.py

import esper
import pygame
import math
from typing import List, Dict, Optional, TYPE_CHECKING
# 類型檢查：假設 Game 類在 src.game 模組中
if TYPE_CHECKING:
    from src.core.game import Game 

# 假設 TILE_SIZE 在 src.config 模組中
from src.core.config import TILE_SIZE 

# 假設這些是您自定義的組件 (Components)
from ..ecs.components import (
    Position, Velocity, Renderable, Collider, Health, Defense, Combat, Buffs, AI, Tag, 
    NPCInteractComponent, DungeonPortalComponent, PlayerComponent, Lifetime
)

# 假設這些是您自定義的 AI 行為和行為樹節點
from ..ecs.ai import (
    EnemyContext,
    ChaseAction, AttackAction, WaitAction, PatrolAction, DodgeAction, 
    SpecialAttackAction, MeleeAttackAction, RandomMoveAction, # 動作類
    RefillActionList, PerformNextAction, Sequence, Selector, ConditionNode # 行為樹節點
)

# 【新增 Facade 類別的導入】
# 確保這些 Facade 類別已在 src.entities.npc 中定義
from ..entities.npc.alchemy_pot_npc import AlchemyPotNPC
from ..entities.npc.dungeon_portal_npc import DungeonPortalNPC
from ..entities.npc.magic_crystal_npc import MagicCrystalNPC


def create_player_entity(
    world: esper, x: float = 0.0, y: float = 0.0, tag: str = "player",game: 'Game' = None
) -> int:
    """
    創建一個 Player ECS 實體並附上所有必要的組件。
    """
    player_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(player_entity, Tag(tag=tag))
    world.add_component(player_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    # 注意：這裡應該載入圖片，但為了簡化，我們只設定屬性
    world.add_component(player_entity, Renderable(
        image=None, 
        shape="rect",
        w=TILE_SIZE,
        h=TILE_SIZE,
        color=(0, 0, 255), # 藍色方塊代表玩家
        layer=1 
    ))

    # 3. 碰撞器
    world.add_component(player_entity, Collider(
        w=TILE_SIZE, 
        h=TILE_SIZE, 
        pass_wall=False, 
        collision_group="player"
    ))

    # 4. 健康與防禦 (Health Component) - 新增 base_max_hp, max_shield, current_shield 欄位
    world.add_component(player_entity, Health(
        max_hp=100,
        current_hp=100,
        regen_rate=1.0,
        base_max_hp=100,  # 初始基底 HP
        max_shield=5,    # 初始基底 Shield
        current_shield=0 # 初始 Shield 值
    ))
    world.add_component(player_entity, Defense(
        defense=5,
        dodge_rate=0.05,
        element="untyped",
        resistances={},
        invulnerable=False
    ))

    # 5. 戰鬥能力
    world.add_component(player_entity, Combat(
        damage=10,
        atk_element="physical",
        collision_cooldown=0.5
    ))

    # 6. 能力增益效果 (Buffs)
    world.add_component(player_entity, Buffs())

    # 7. 玩家專屬組件 (PlayerComponent) - 新增 base_max_speed, base_energy_regen_rate 等欄位
    world.add_component(player_entity, PlayerComponent(
        skill_chain=[],
        energy=100,
        max_energy=100,
        energy_regen_rate=5.0,
        base_energy_regen_rate=5.0,  # 初始基底能量回覆
        fog=True,
        vision_radius=10
    ))

    # 8. tag組件
    world.add_component(player_entity, Tag(tag="player"))
    
    # 9. 速度組件
    world.add_component(player_entity, Velocity(
        x=0.0,
        y=0.0,
        speed=4*TILE_SIZE # 基底移動速度
    ))
    
    # 10. 渲染組件
    world.add_component(player_entity, Renderable(
        image=None,
        shape="rect",
        w=TILE_SIZE,
        h=TILE_SIZE,
        color=(0, 0, 255), # 藍色方塊代表玩家
        layer=1 
    ))
    
    return player_entity

def create_enemy1_entity(
    world: esper, x: float = 0.0, y: float = 0.0, game: 'Game' = None, tag: str = "enemy",
    base_max_hp: int = 100, max_speed: float = 2 * TILE_SIZE, element: str = "fire", 
    defense: int = 10, damage: int = 5, w: int = TILE_SIZE // 2, h: int = TILE_SIZE // 2,
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
        for bullet in context.get_entities_with_tag("player"):
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
    ])
    
    # 根節點
    behavior_tree = Selector([
        # Emergency check: if not alive, should be removed by HealthSystem
        # ConditionNode(lambda e, t: not e.is_alive(), PlaceholderAction(action_id='die'), # Assuming PlaceholderAction exists
        # Main combat/patrol loop
        perform_action_sequence,
        refill_node
    ])
    
    # 3. 附加組件
    
    # 幾何與運動
    world.add_component(enemy, Position(x=x, y=y))
    world.add_component(enemy, Velocity(speed=max_speed, x=0.0, y=0.0))
    world.add_component(enemy, Collider(w=w, h=h))
    
    # 健康與戰鬥
    world.add_component(enemy, Health(max_hp=base_max_hp, current_hp=base_max_hp))
    world.add_component(enemy, Defense(defense=defense, dodge_rate=0.0, element=element, invulnerable=False))
    world.add_component(enemy, Combat(damage=damage, atk_element=element, collision_cooldown=0.1))
    world.add_component(enemy, Buffs())
    world.add_component(enemy, Tag(tag=tag))
    
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
    invulnerable: bool = True,
    game: 'Game' = None # 【新增 game 參數以初始化 Facade】
) -> int:
    """創建一個 ECS 煉金鍋 NPC 實體。"""
    
    npc_entity = world.create_entity() # <--- 變數名稱修正為 npc_entity

    # 1. 核心位置與標籤
    world.add_component(npc_entity, Tag(tag=tag))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
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

    # 6. 煉金鍋專屬狀態 (交互組件)
    world.add_component(npc_entity, NPCInteractComponent()) 

    # 【新增 Facade 初始化邏輯】
    if game:
        # 這會調用 AlchemyPotNPC.__init__，將 start_interaction 方法連結到 NPCInteractComponent 上
        AlchemyPotNPC(game, npc_entity) 
    # ---------------------------------
    
    return npc_entity

def create_dungeon_portal_npc(
    world: esper,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 64, 
    h: int = 64, 
    available_dungeons: Optional[List[Dict]] = None,
    game: 'Game' = None # 【新增 game 參數以初始化 Facade】
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

    # 【新增 Facade 初始化邏輯】
    if game:
        # 這會調用 DungeonPortalNPC.__init__，將 start_interaction 方法連結到 NPCInteractComponent 上
        DungeonPortalNPC(game, npc_entity)
        print(f"DungeonPortalNPC created with entity ID: {npc_entity}")
    # ---------------------------------

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
    invulnerable: bool = True,
    game: 'Game' = None # 【新增 game 參數以初始化 Facade】
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

    # 【新增 Facade 初始化邏輯】
    if game:
        # 這會調用 MagicCrystalNPC.__init__，將 start_interaction 方法連結到 NPCInteractComponent 上
        MagicCrystalNPC(game, npc_entity) 
    # ---------------------------------

    return npc_entity

def create_dummy_entity(
    world: esper,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 32, 
    h: int = 32, 
    tag: str = "dummy_npc",
    game: 'Game' = None # 【新增 game 參數以初始化 Facade】
) -> int:
    """創建一個簡單的 ECS NPC 實體作為佔位符。"""
    
    npc_entity = world.create_entity()

    # 1. 核心位置與標籤
    world.add_component(npc_entity, Tag(tag=tag))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺屬性
    world.add_component(npc_entity, Renderable(
        image=None, 
        shape="rect",
        w=w,
        h=h,
        color=(200, 200, 200), # 灰色
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
    world.add_component(npc_entity, Health(max_hp=99999999, current_hp=99999999,regen_rate=99999999))
    world.add_component(npc_entity, Defense(
        defense=0,
        element="untyped",
        invulnerable=False
    ))
    world.add_component(npc_entity, Combat(
        damage=0,
        atk_element="untyped",
        collision_cooldown=0.0
    ))
    
    
    # 5. 增益效果 (Buffs)
    world.add_component(npc_entity, Buffs())

    return npc_entity

def create_damage_text_entity(
    world: esper,
    x: float = 0.0,
    y: float = 0.0,
    damage: int = 0,
    color: tuple = (255, 0, 0),
    duration: float = 1.0,
) -> int:
    """創建一個顯示傷害數字的實體。"""
    
    damage_text_entity = world.create_entity()

    # 1. 位置組件
    world.add_component(damage_text_entity, Position(x=x, y=y))
    world.add_component(damage_text_entity, Velocity(x=0.0, y=-30.0)) # 向上移動
    # 2. 渲染組件
    font = pygame.font.SysFont('Arial', 24)
    text_surface = font.render(str(damage), True, color)
    world.add_component(damage_text_entity, Renderable(
        image=text_surface,
        shape="text",
        w=text_surface.get_width(),
        h=text_surface.get_height(),
        color=color,
        layer=2 
    ))

    # 3. 壽命組件 (用於控制顯示時間)
    world.add_component(damage_text_entity, Lifetime(max_lifetime=duration))

    return damage_text_entity

def create_boss_entity(
    world: esper, x: float = 0.0, y: float = 0.0, game: 'Game' = None, 
    boss_id: str = "boss_dark_king"
) -> int:
    """創建 Boss 實體"""
    # 簡單起見，基於 enemy1 但更強大
    print(f"Creating Boss {boss_id} at {x}, {y}")
    boss = create_enemy1_entity(
        world, x, y, game, tag="boss",
        base_max_hp=5000,
        damage=50,
        w=TILE_SIZE * 2, h=TILE_SIZE * 2, # 2x2 大小
        defense=50
    )
    # 可能添加 Boss 組件以便系統識別
    return boss

def create_win_npc_entity(
    world: esper,
    x: float = 0.0, 
    y: float = 0.0, 
    w: int = 64, 
    h: int = 64, 
    game: 'Game' = None
) -> int:
    """創建與 WinMenu 關聯的 Final NPC"""
    
    npc_entity = world.create_entity()

    # 1. 核心
    world.add_component(npc_entity, Tag(tag="win_npc"))
    world.add_component(npc_entity, Position(x=x, y=y))
    
    # 2. 視覺 (金色?)
    world.add_component(npc_entity, Renderable(
        image=None,
        shape="rect",
        w=w,
        h=h,
        color=(255, 215, 0), # 金色
        layer=0 
    ))

    # 3. 碰撞器
    world.add_component(npc_entity, Collider(w=w, h=h, pass_wall=False, collision_group="npc"))
    world.add_component(npc_entity, Health(max_hp=999999, current_hp=999999))
    world.add_component(npc_entity, Defense(defense=100, element="untyped", invulnerable=True))
    world.add_component(npc_entity, Buffs())

    # 4. 交互
    world.add_component(npc_entity, NPCInteractComponent(interaction_range=80.0))
    
    # Facade 初始化 - 這裡需要一個 Facade 類來打開 WinMenu
    # 由於我們還沒創建 WinNPC Facade，我們可以暫時借用 DungeonPortalNPC 的邏輯，或者直接在這裡注入 lambda ?
    # 為了架構正確性，我們稍後應該創建 src/entities/npc/win_npc.py
    # 暫時解決：在 EntityManager 中手動綁定 interaction 或者在這裡創建一個臨時的交互邏輯
    
    # 如果 WinMenu 已存在，我們可以讓它打開 WinMenu
    if game:
        def open_win_menu():
            print("Win NPC Interacted -> Opening Win Menu")
            game.menu_manager.open_menu("win_menu") # 假設 MenuManager 有這個 key
            
        interact_comp = world.component_for_entity(npc_entity, NPCInteractComponent)
        interact_comp.start_interaction = open_win_menu

    return npc_entity