# src/entity_manager.py (ECS Refactoring)

from typing import List, Tuple, Dict, Optional
import esper
import pygame
import random

# 引入 ECS 實體工廠函數 (假設這些工廠函數已經在 ecs_factory.py 中定義)
from src.entities.ecs_factory import (
    create_player_entity, create_alchemy_pot_npc, create_magic_crystal_npc, 
    create_dungeon_portal_npc, create_dummy_entity, create_enemy1_entity
)
# 引入 Player Facade (假設這是玩家實體的外部接口)
from src.entities.player.player import Player 
# 引入 ECS 組件 (用於清理和位置操作)
from src.ecs.components import Position, NPCInteractComponent, PlayerComponent
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

class EntityManager:
    """
    實體管理器 (ECS Wrapper)。
    負責管理 esper.World、實體的生成、清除和與 Game 核心邏輯的集成。
    """
    def __init__(self, game: 'Game'):
        """初始化實體管理器。"""
        self.game = game 
        # 實體管理的核心：esper.World 實例
        self.world: esper = esper 
        # 玩家 Facade，用於外部系統調用 (如 storage_manager.apply_all_to_player())
        self.player: Optional['Player'] = None 
        
        # 移除 Pygame sprite groups，ECS 通過實體 ID 管理
        # self.entity_group = pygame.sprite.Group() 
        # self.bullet_group = pygame.sprite.Group() 
        # self.damage_text_group = pygame.sprite.Group()

    # --- Utility Methods (保持不變) ---

    def get_valid_tiles(self, room, tile_types: List[str]) -> List[Tuple[int, int]]:
        """獲取房間中指定類型的有效瓦片位置（全局座標）。"""
        valid_tiles = []
        for y in range(int(room.height)):
            for x in range(int(room.width)):
                tile_type = room.tiles[y][x]
                if tile_type in tile_types:
                    valid_tiles.append((room.x + x, room.y + y)) 
        return valid_tiles

    def tile_to_pixel(self, tile_x: int, tile_y: int) -> Tuple[float, float]:
        """將瓦片座標轉換為像素座標（瓦片中心）。"""
        return (tile_x * TILE_SIZE + TILE_SIZE / 2, tile_y * TILE_SIZE + TILE_SIZE / 2)

    # --- ECS 初始化與生成 ---
    
    def initialize_lobby_entities(self, room) -> None:
        """初始化大廳房間的 ECS 實體，使用工廠函數生成。"""
        self.clear_entities() 
        
        spawn_map: Dict[str, List[str]] = {
            'player': ['Player_spawn'],
            'alchemy_pot_npc': ['Alchemy_pot_NPC_spawn'],
            'magic_crystal_npc': ['Magic_crystal_NPC_spawn'],
            'dungeon_portal_npc': ['Dungeon_portal_NPC_spawn'],
            'dummy_entity': ['Dummy_spawn'] 
        }
        fallback_tiles = self.get_valid_tiles(room, ['Lobby_room_floor', 'Room_floor'])
        used_tiles = set()
        
        # 1. 初始化玩家
        player_tiles = self.get_valid_tiles(room, spawn_map['player'])
        player_x, player_y, player_tile = 0.0, 0.0, None

        if player_tiles:
            player_tile = player_tiles[0] 
        elif fallback_tiles:
            player_tile = random.choice(fallback_tiles)
        
        if player_tile:
            player_x, player_y = self.tile_to_pixel(*player_tile)
            used_tiles.add(player_tile)
        else:
            player_x, player_y = self.game.dungeon_manager.get_room_center(room)
            
        # 使用 ECS Factory 創建玩家實體，並儲存 Facade
        player_ecs_id = create_player_entity(self.world, x=player_x, y=player_y) 
        self.player = Player(self.game, player_ecs_id)
        
        self.game.storage_manager.apply_all_to_player() 
        print(f"EntityManager: 初始化玩家實體 ID: {player_ecs_id}，像素座標 ({player_x}, {player_y})")
            
        # 2. 初始化 NPC (使用工廠函數)
        npc_configs: List[Tuple[callable, str]] = [
            (create_alchemy_pot_npc, 'alchemy_pot_npc'),
            (create_magic_crystal_npc, 'magic_crystal_npc'),
            (create_dungeon_portal_npc, 'dungeon_portal_npc'),
            (create_dummy_entity, 'dummy_entity')
        ]

        for factory_func, npc_key in npc_configs:
            npc_tiles = self.get_valid_tiles(room, spawn_map[npc_key])
            npc_x, npc_y, npc_tile = 0.0, 0.0, None
            
            if npc_tiles:
                npc_tile = npc_tiles[0]
            elif fallback_tiles:
                available_tiles = [t for t in fallback_tiles if t not in used_tiles]
                if available_tiles:
                    npc_tile = random.choice(available_tiles)
            
            if npc_tile:
                npc_x, npc_y = self.tile_to_pixel(*npc_tile)
                
                # 處理需要額外參數的 Dungeon Portal
                if npc_key == 'dungeon_portal_npc':
                    npc_entity_id = factory_func(
                        self.world, x=npc_x, y=npc_y,
                        available_dungeons=[{'name': 'Test Dungeon', 'level': 1, 'room_id': 1}],
                        game=self.game
                    )
                else:
                    npc_entity_id = factory_func(self.world, x=npc_x, y=npc_y,game=self.game)

                used_tiles.add(npc_tile)
                print(f"EntityManager: 初始化 {npc_key} 實體 ID: {npc_entity_id}")
            else:
                print(f"EntityManager: 無有效瓦片可供 {npc_key}，跳過")

        print(f"EntityManager: 總共創建了 {len(self.world._entities)} 個實體。")


    def initialize_dungeon_entities(self) -> None:
        """初始化地牢房間的 ECS 實體，使用工廠函數生成並重定位玩家。"""
        self.clear_entities() 
        dungeon = self.game.dungeon_manager.dungeon
        
        for y in range(int(dungeon.grid_height)):
            for x in range(int(dungeon.grid_width)):
                tile_type = dungeon.dungeon_tiles[y][x]
                entity_x, entity_y = self.tile_to_pixel(x, y)
                
                if tile_type == 'Monster_spawn':
                    # 創建敵人實體 (使用工廠函數)
                    create_enemy1_entity(self.world, x=entity_x, y=entity_y) 
                    
                elif tile_type == 'End_room_portal':
                    # 創建地牢傳送門實體 (使用工廠函數)
                    create_dungeon_portal_npc(
                        self.world, x=entity_x, y=entity_y,
                        available_dungeons=[{'name': 'Test Dungeon', 'level': 1, 'room_id': 1}],
                        game=self.game
                    )
                    
                        
                elif tile_type == 'Player_spawn':
                    if self.player:
                        # 移動玩家實體的位置組件 (使用 Facade)
                        pos_comp = self.world.component_for_entity(self.player.ecs_entity, Position)
                        pos_comp.x, pos_comp.y = entity_x, entity_y
                        print(f"EntityManager: 在瓦片 ({x}, {y}) 重定位玩家，像素座標 ({entity_x}, {entity_y})")
                    else:
                        # 創建新玩家 (防禦性編程)
                        player_ecs_id = create_player_entity(self.world, x=entity_x, y=entity_y) 
                        self.player = Player(self.game, player_ecs_id)
                        
                    self.game.storage_manager.apply_all_to_player() 
                    self.game.render_manager.camera_offset = [entity_x - SCREEN_WIDTH // 2, entity_y - SCREEN_HEIGHT // 2] 

        self.game.render_manager.reset_minimap() 
        self.game.render_manager.reset_fog() 


    # --- ECS 核心循環集成 (移除) ---

    def update(self, dt: float, current_time: float) -> None:
        """
        [已被 ECS 取代] 實體更新邏輯已移至 ECS Systems。
        遊戲主循環應直接呼叫 self.world.process(dt, current_time)。
        """
        # 僅用於調試或舊代碼兼容，但在 ECS 結構中應移除此處的循環邏輯
        pass 

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """
        [已被 ECS 取代] 實體繪製邏輯已移至 RenderSystem。
        """
        pass
    
    # --- ECS 清理方法 ---

    def clear_entities(self) -> None:
        """
        清除所有非玩家實體。
        """
        player_id = self.player.ecs_entity if self.player else None
        entities_to_delete = []
        for entity_id in self.world._entities:
            # 確保不會刪除玩家實體
            if entity_id != player_id: 
                entities_to_delete.append(entity_id)

        # 批量刪除實體
        for entity_id in entities_to_delete:
            self.world.delete_entity(entity_id)
            
        # 注意: 投射物和傷害文字現在也應通過它們的 ECS ID 被刪除
        # 假設它們已包含在上面的 world._entities 列表中
        
        print(f"EntityManager: 已清除 {len(entities_to_delete)} 個非玩家實體。")
    
    def get_interactable_entities(self) -> List[Tuple[int, Position, 'NPCInteractComponent']]:
        """
        獲取所有具有 NPCInteractComponent 的可交互實體。
        返回一個包含實體 ID、位置組件和交互組件的元組列表。
        """
        interactable_entities = []
        for entity_id, (pos_comp, interact_comp) in self.world.get_components(Position, NPCInteractComponent):
            interactable_entities.append((entity_id, pos_comp, interact_comp))
        return interactable_entities

    def get_player_component(self) -> Optional[Tuple[Position]]:
        """
        獲取玩家實體的組件元組。
        返回包含玩家位置組件的元組，或 None 如果玩家不存在。
        """
        if self.player:
            try:
                player_comp = self.world.component_for_entity(self.player.ecs_entity, PlayerComponent)
                return player_comp
            except KeyError:
                print("EntityManager: 玩家實體缺少 Position 組件。")
                return None
        return None
    
    def get_all_entities(self) -> List[int]:
        """
        獲取所有實體的 ID 列表。
        """
        return list(self.world._entities)