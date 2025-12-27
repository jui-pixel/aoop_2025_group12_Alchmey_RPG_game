import unittest
import sys
import os
from unittest.mock import MagicMock

# ==========================================
# 0. 路徑設定
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ==========================================
# 1. 設置 Global Mock (針對依賴項)
# ==========================================
mock_modules_dict = {
    'esper': MagicMock(),
    'pygame': MagicMock(),
    'src.core': MagicMock(),
    'src.core.game': MagicMock(),
    'src.core.config': MagicMock(),
    'src.ecs': MagicMock(),
    'src.ecs.components': MagicMock(),
    'src.ecs.ai': MagicMock(),
    'src.entities.npc': MagicMock(),
    
    # 這裡我們建立具體的 Mock 物件，以便稍後在測試中引用它們
    'src.entities.npc.alchemy_pot_npc': MagicMock(),
    'src.entities.npc.dungeon_portal_npc': MagicMock(),
    'src.entities.npc.magic_crystal_npc': MagicMock(),
    'src.entities.npc.trader_npc': MagicMock(),
    'src.entities.npc.treasure_npc': MagicMock(),
}

mock_modules_dict['src.core.config'].TILE_SIZE = 32

for mod_name, mod_obj in mock_modules_dict.items():
    sys.modules[mod_name] = mod_obj

# ==========================================
# 2. 定義假的 Components 和 Classes
# ==========================================
class MockComponent:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

class Position(MockComponent): pass
class Velocity(MockComponent): pass
class Health(MockComponent): pass
class Defense(MockComponent): pass
class Combat(MockComponent): pass
class Renderable(MockComponent): pass
class Collider(MockComponent): pass
class Tag(MockComponent): pass
class AI(MockComponent): pass
class NPCInteractComponent(MockComponent): pass
class DungeonPortalComponent(MockComponent): pass
class PlayerComponent(MockComponent): pass
class Buffs(MockComponent): pass
class TimerComponent(MockComponent): pass
class TreasureStateComponent(MockComponent): pass
class BossComponent(MockComponent): pass

sys.modules['src.ecs.components'].Position = Position
sys.modules['src.ecs.components'].Velocity = Velocity
sys.modules['src.ecs.components'].Health = Health
sys.modules['src.ecs.components'].Defense = Defense
sys.modules['src.ecs.components'].Combat = Combat
sys.modules['src.ecs.components'].Renderable = Renderable
sys.modules['src.ecs.components'].Collider = Collider
sys.modules['src.ecs.components'].Tag = Tag
sys.modules['src.ecs.components'].AI = AI
sys.modules['src.ecs.components'].NPCInteractComponent = NPCInteractComponent
sys.modules['src.ecs.components'].DungeonPortalComponent = DungeonPortalComponent
sys.modules['src.ecs.components'].PlayerComponent = PlayerComponent
sys.modules['src.ecs.components'].Buffs = Buffs
sys.modules['src.ecs.components'].TimerComponent = TimerComponent
sys.modules['src.ecs.components'].TreasureStateComponent = TreasureStateComponent
sys.modules['src.ecs.components'].BossComponent = BossComponent

class ActionNode: 
    def __init__(self, **kwargs): pass
class Sequence: 
    def __init__(self, children): self.children = children
class Selector: 
    def __init__(self, children): self.children = children
class RefillActionList: 
    def __init__(self, actions, logic): pass
class PerformNextAction:
    def __init__(self, actions): pass

ai_mocks = [
    'DashAction', 'DashBackAction', 'StrafeAction', 'TauntAction', 
    'ChaseAction', 'AttackAction', 'FanAttackAction', 'RadialBurstAction', 
    'WaitAction', 'PatrolAction', 'DodgeAction', 'SpecialAttackAction', 
    'MeleeAttackAction', 'RandomMoveAction', 'ConditionNode', 'EnemyContext'
]
for ai_cls in ai_mocks:
    setattr(sys.modules['src.ecs.ai'], ai_cls, MagicMock())

sys.modules['src.ecs.ai'].Sequence = Sequence
sys.modules['src.ecs.ai'].Selector = Selector
sys.modules['src.ecs.ai'].RefillActionList = RefillActionList
sys.modules['src.ecs.ai'].PerformNextAction = PerformNextAction

# ==========================================
# 3. 導入待測模組
# ==========================================
try:
    from src.entities.ecs_factory import (
        create_player_entity,
        create_enemy1_entity,
        create_alchemy_pot_npc,
        create_boss_entity,
        create_dungeon_portal_npc
    )
except ImportError as e:
    raise ImportError(f"導入失敗: {e}")

# ==========================================
# 4. 測試類別
# ==========================================
class TestECSFactory(unittest.TestCase):

    def setUp(self):
        self.mock_world = MagicMock()
        self.mock_world.create_entity.return_value = 12345 
        self.mock_game = MagicMock()

    def assertComponentAdded(self, entity_id, component_type, **attrs):
        found = False
        for call in self.mock_world.add_component.call_args_list:
            args, _ = call
            if args[0] == entity_id and isinstance(args[1], component_type):
                comp = args[1]
                match = True
                for k, v in attrs.items():
                    if getattr(comp, k, None) != v:
                        match = False
                        break
                if match:
                    found = True
                    break
        self.assertTrue(found, f"Component {component_type.__name__} with attrs {attrs} not found on entity {entity_id}")

    def test_create_player_entity(self):
        entity_id = create_player_entity(self.mock_world, x=100, y=200, game=self.mock_game)
        self.assertEqual(entity_id, 12345)
        self.assertComponentAdded(entity_id, Position, x=100, y=200)

    def test_create_enemy1_entity(self):
        entity_id = create_enemy1_entity(self.mock_world, x=50, y=50, game=self.mock_game, element="fire")
        self.assertComponentAdded(entity_id, Position, x=50, y=50)
        self.assertComponentAdded(entity_id, Health, max_hp=100)

    def test_create_alchemy_pot_npc(self):
        """測試煉金鍋 NPC (修正版)"""
        # 1. 直接從我們設定的 sys.modules 中導入 Mock 類別
        # 由於 ecs_factory 也是從這裡導入的，這會是同一個物件實例
        from src.entities.npc.alchemy_pot_npc import AlchemyPotNPC as MockAlchemyFacade
        
        # 2. 重置這個 Mock 的狀態，確保之前的測試不會影響這裡
        MockAlchemyFacade.reset_mock()
        
        entity_id = create_alchemy_pot_npc(self.mock_world, x=10, y=20, game=self.mock_game)
        
        self.assertComponentAdded(entity_id, Tag, tag="alchemy_pot_npc")
        
        # 3. 直接驗證導入的 Mock 是否被呼叫
        MockAlchemyFacade.assert_called_once_with(self.mock_game, entity_id)

    def test_create_dungeon_portal_npc(self):
        """測試傳送門 NPC (修正版)"""
        dungeons = [{'name': 'Test', 'level': 1}]
        
        # 1. 導入 Mock
        from src.entities.npc.dungeon_portal_npc import DungeonPortalNPC as MockPortalFacade
        
        # 2. 重置
        MockPortalFacade.reset_mock()
        
        entity_id = create_dungeon_portal_npc(
            self.mock_world, x=0, y=0, available_dungeons=dungeons, game=self.mock_game
        )
        
        self.assertComponentAdded(entity_id, DungeonPortalComponent, available_dungeons=dungeons)
        
        # 3. 驗證
        MockPortalFacade.assert_called_once_with(self.mock_game, entity_id)

    def test_create_boss_entity(self):
        boss_id = "boss_test"
        entity = create_boss_entity(self.mock_world, x=300, y=300, game=self.mock_game, boss_id=boss_id)
        self.assertComponentAdded(entity, BossComponent, boss_name=boss_id)

if __name__ == '__main__':
    print("Running ECS Factory Tests...")
    unittest.main(verbosity=2)