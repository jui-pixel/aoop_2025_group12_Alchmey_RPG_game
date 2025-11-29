# src/entity_manager.py
from typing import List, Tuple
from src.entities.player.player import Player
from src.entities.npc.alchemy_pot_npc import AlchemyPotNPC
from src.entities.npc.magic_crystal_npc import MagicCrystalNPC
from src.entities.npc.dungeon_portal_npc import DungeonPortalNPC
from src.entities.bullet.bullet import Bullet
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
from src.entities.enemy.enemy1 import Enemy1
import pygame
import random

class EntityManager:
    def __init__(self, game: 'Game'):
        """初始化實體管理器，負責管理玩家、NPC、敵人和投射物。

        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.game = game  # 保存遊戲實例引用
        self.player = None  # 玩家實例，初始為空
        self.entity_group = pygame.sprite.Group()  # 實體(玩家/NPC/敵人)精靈組
        self.bullet_group = pygame.sprite.Group()  # 投射物精靈組
        self.damage_text_group = pygame.sprite.Group()  # 傷害文字精靈組

    def get_valid_tiles(self, room, tile_types: List[str]) -> List[Tuple[int, int]]:
        """獲取房間中指定類型的有效瓦片位置（全局座標）。

        Args:
            room: 要檢查的房間實例。
            tile_types: 允許的瓦片類型列表。

        Returns:
            List[Tuple[int, int]]: 有效瓦片位置的列表（全局座標）。
        """
        valid_tiles = []
        for y in range(int(room.height)):
            for x in range(int(room.width)):
                tile_type = room.tiles[y][x]
                if tile_type in tile_types:
                    valid_tiles.append((room.x + x, room.y + y))  # 將房間本地座標轉換為全局座標
        return valid_tiles

    def tile_to_pixel(self, tile_x: int, tile_y: int) -> Tuple[float, float]:
        """將瓦片座標轉換為像素座標（瓦片中心）。

        Args:
            tile_x: 瓦片的 x 座標。
            tile_y: 瓦片的 y 座標。

        Returns:
            Tuple[float, float]: 對應的像素座標 (x, y)。
        """
        return (tile_x * TILE_SIZE + TILE_SIZE / 2, tile_y * TILE_SIZE + TILE_SIZE / 2)

    def initialize_lobby_entities(self, room) -> None:
        """初始化大廳房間的實體，將其放置在指定瓦片上。

        Args:
            room: 大廳房間實例。

        根據瓦片類型生成玩家和 NPC，若無特定瓦片則使用備用瓦片或房間中心。
        """
        self.clear_entities()  # 清除現有實體和投射物，保留玩家實例
        spawn_map = {
            'Player': ['Player_spawn'],  # 玩家生成瓦片
            'AlchemyPotNPC': ['Alchemy_pot_NPC_spawn'],  # 煉金鍋 NPC 生成瓦片
            'MagicCrystalNPC': ['Magic_crystal_NPC_spawn'],  # 魔法水晶 NPC 生成瓦片
            'DungeonPortalNPC': ['Dungeon_portal_NPC_spawn'],  # 地牢入口 NPC 生成瓦片
            'Dummy': ['Dummy_spawn']  # 假人敵人生成瓦片
        }
        fallback_tiles = self.get_valid_tiles(room, ['Lobby_room_floor', 'Room_floor'])  # 備用地板瓦片

        # 初始化玩家
        player_tiles = self.get_valid_tiles(room, spawn_map['Player'])
        if player_tiles:
            player_tile = player_tiles[0]  # 使用第一個玩家生成瓦片
            player_x, player_y = self.tile_to_pixel(*player_tile)
            self.player = Player(x=player_x, y=player_y, game=self.game, pass_wall=False, tag="player")  # 生成玩家（可穿牆）
            print(f"EntityManager: 在瓦片 ({player_tile[0]}, {player_tile[1]}) 初始化玩家，像素座標 ({player_x}, {player_y})")
        elif fallback_tiles:
            player_tile = random.choice(fallback_tiles)  # 隨機選擇備用地板瓦片
            player_x, player_y = self.tile_to_pixel(*player_tile)
            self.player = Player(x=player_x, y=player_y, game=self.game, tag="player")  # 生成玩家（不可穿牆）
            print(f"EntityManager: 在備用地板瓦片 ({player_tile[0]}, {player_tile[1]}) 初始化玩家，像素座標 ({player_x}, {player_y})")
        else:
            center_x, center_y = self.game.dungeon_manager.get_room_center(room)  # 使用房間中心
            self.player = Player(x=center_x, y=center_y, game=self.game, tag="player")
            print(f"EntityManager: 在房間中心 ({center_x}, {center_y}) 初始化玩家 - 無有效瓦片")
        self.game.storage_manager.apply_all_to_player()  # Apply stored stats and skills to player
        self.entity_group.add(self.player)
        # 初始化 NPC
        # self.entity_group.empty()  # 清空現有 NPC
        npc_classes = [
            (AlchemyPotNPC, 'AlchemyPotNPC'),
            (MagicCrystalNPC, 'MagicCrystalNPC'),
            (lambda x, y, game: DungeonPortalNPC(x=x, y=y, game=game, 
                                                available_dungeons=[{'name': 'Test Dungeon', 'level': 1, 'room_id': 1}]), 
             'DungeonPortalNPC'),
            (Dummy, 'Dummy')
        ]
        used_tiles = {player_tile} if player_tiles or fallback_tiles else set()  # 記錄已使用的瓦片

        for npc_class, npc_key in npc_classes:
            npc_tiles = self.get_valid_tiles(room, spawn_map[npc_key])
            if npc_tiles:
                npc_tile = npc_tiles[0]  # 使用第一個特定生成瓦片
                npc_x, npc_y = self.tile_to_pixel(*npc_tile)
                self.entity_group.add(npc_class(x=npc_x, y=npc_y, game=self.game))  # 添加 NPC
                used_tiles.add(npc_tile)
                print(f"EntityManager: 在瓦片 ({npc_tile[0]}, {npc_tile[1]}) 初始化 {npc_key}，像素座標 ({npc_x}, {npc_y})")
            elif fallback_tiles:
                available_tiles = [t for t in fallback_tiles if t not in used_tiles]  # 獲取未使用的備用瓦片
                if available_tiles:
                    npc_tile = random.choice(available_tiles)
                    npc_x, npc_y = self.tile_to_pixel(*npc_tile)
                    self.entity_group.add(npc_class(x=npc_x, y=npc_y, game=self.game))  # 添加 NPC
                    used_tiles.add(npc_tile)
                    print(f"EntityManager: 在備用地板瓦片 ({npc_tile[0]}, {npc_tile[1]}) 初始化 {npc_key}，像素座標 ({npc_x}, {npc_y})")
                else:
                    print(f"EntityManager: 無有效瓦片可供 {npc_key}，跳過")
            else:
                print(f"EntityManager: 無有效瓦片可供 {npc_key}，跳過")

        print(f"EntityManager: 初始化了 {len(self.entity_group)} 個 NPC")

    def initialize_dungeon_entities(self) -> None:
        """初始化地牢房間的實體，將其放置在指定瓦片上。

        Args:
            room: 地牢房間實例。

        根據瓦片類型生成敵人，若無特定瓦片則使用備用瓦片或房間中心。
        """
        spawn_map = {
            'Player': ['Player_spawn'],  # 玩家生成瓦片
            'Enemy1': ['Monster_spawn'],  # 敵人1生成瓦片
        }
        self.clear_entities()  # 清除現有實體和投射物，保留玩家實例
        # 初始化敵人
        for y in range(int(self.game.dungeon_manager.dungeon.grid_height)):
            for x in range(int(self.game.dungeon_manager.dungeon.grid_width)):
                if self.game.dungeon_manager.dungeon.dungeon_tiles[y][x] == 'Monster_spawn':
                    enemy_x, enemy_y = self.tile_to_pixel(x, y)
                    self.entity_group.add(Enemy1(x=enemy_x, y=enemy_y, game=self.game, tag="enemy"))  # 添加敵人
                elif self.game.dungeon_manager.dungeon.dungeon_tiles[y][x] == 'End_room_portal':
                    if not any(isinstance(e, DungeonPortalNPC) for e in self.entity_group):
                        portal_x, portal_y = self.tile_to_pixel(x, y)
                        self.entity_group.add(DungeonPortalNPC(x=portal_x, y=portal_y, game=self.game, 
                                                               available_dungeons=[{'name': 'Test Dungeon', 'level': 1, 'room_id': 1}]))  # 添加地牢入口 NPC
                    
                elif self.game.dungeon_manager.dungeon.dungeon_tiles[y][x] == 'Player_spawn':
                    if not self.player:
                        player_x, player_y = self.tile_to_pixel(x, y)
                        self.player = Player(x=player_x, y=player_y, game=self.game)  # 生成玩家（不可穿牆）
                        self.entity_group.add(self.player)
                        self.game.storage_manager.apply_all_to_player()  # Apply stored stats and skills to player
                        print(f"EntityManager: 在瓦片 ({x}, {y}) 初始化玩家，像素座標 ({player_x}, {player_y})")
                    else:
                        self.player.x, self.player.y = self.tile_to_pixel(x, y)
                    self.game.render_manager.camera_offset = [self.player.x - SCREEN_WIDTH // 2, self.player.y - SCREEN_HEIGHT // 2] # 初始化攝影機位置
        self.game.render_manager.reset_minimap()  # 重置小地圖
        self.game.render_manager.reset_fog()  # 重置迷霧
        
    def update(self, dt: float, current_time: float) -> None:
        """更新所有實體的狀態。

        Args:
            dt: 每幀的時間間隔（秒）。
            current_time: 當前遊戲時間。

        更新玩家、NPC、敵人和投射物的狀態。
        """
        # if self.player:
        #     self.player.update(dt, current_time)  # 更新玩家
        for entity in self.entity_group:
            entity.update(dt, current_time)  # 更新每個 實體
        for entity in self.bullet_group:
            entity.update(dt, current_time)  # 更新每個 投射物
        for entity in self.damage_text_group:
            entity.update(dt, current_time)  # 更新每個傷害文字
        print(f"EntityManager: 在狀態 {self.game.event_manager.state} 中更新實體")

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """繪製所有實體。

        Args:
            screen: Pygame 的顯示表面。
            camera_offset: 攝影機偏移量，用於調整渲染位置。

        繪製 NPC、敵人、投射物和玩家。
        """
        for entity in self.entity_group:
            entity.draw(screen, camera_offset)  # 繪製每個 實體
        for entity in self.bullet_group:
            entity.draw(screen, camera_offset)  # 繪製每個  投射物
        for entity in self.damage_text_group:
            entity.draw(screen, camera_offset)  # 繪製每個傷害文字  
        if self.player:
            self.player.draw(screen, camera_offset)  # 繪製玩家
    
    def clear_entities(self) -> None:
        """清除所有實體和投射物，保留玩家實例。

        用於重置房間或場景時。
        """
        self.entity_group.empty()  # 清空所有 實體
        self.bullet_group.empty()  # 清空所有 投射物
        self.damage_text_group.empty()  # 清空所有 傷害文字
        if self.player:
            self.entity_group.add(self.player)  # 保留玩家實例
        print("EntityManager: 已清除所有實體和投射物，保留玩家")