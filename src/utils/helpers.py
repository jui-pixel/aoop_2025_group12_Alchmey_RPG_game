# src/utils/helpers.py
import os
from typing import Dict
import pygame
from src.dungeon.config.dungeon_config import DungeonConfig
from src.config import DARK_GRAY, GRAY

def get_project_path(*subpaths):
    """Get the absolute path to the project root (roguelike_dungeon/) and join subpaths."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(project_root, *subpaths)

def load_tileset(config, get_project_path, tile_mapping: Dict[str, str]) -> Dict[str, pygame.Surface]:
    """通用 Tileset 載入函數，處理縮放和回退邏輯。"""
    tileset = {}
    tileset_dir = get_project_path("assets", "tiles")
    tile_size = config.tile_size
    
    for tile_type, filename in tile_mapping.items():
        file_path = os.path.join(tileset_dir, filename)
        try:
            image = pygame.image.load(file_path).convert_alpha()
            # Scale image to TILE_SIZE if needed
            if image.get_width() != tile_size or image.get_height() != tile_size:
                image = pygame.transform.scale(image, (tile_size, tile_size))
            tileset[tile_type] = image
        except pygame.error as e:
            print(f"無法載入圖塊 {file_path}: {e}")
            
            # 創建回退彩色 Surface
            fallback = pygame.Surface((tile_size, tile_size))
            
            # 使用 Config 的通行性檢查來決定回退顏色
            is_passable = config.is_tile_passable(tile_type)
            # 這裡假定 DARK_GRAY 和 GRAY 已在頂層導入
            fallback.fill(GRAY if is_passable else DARK_GRAY) 
            tileset[tile_type] = fallback

    return tileset


def load_background_tileset(config: DungeonConfig, get_project_path) -> Dict[str, pygame.Surface]:
    """載入背景貼圖集。"""
    # 這裡應該定義所有背景瓦片 (地板、門、Spawn點) 的映射
    tile_mapping = {
        # 邊界牆變體
        'Border_wall': 'Tileset_1_1.png',
        'Border_wall_top': 'Tileset_0_1.png',
        'Border_wall_bottom': 'Tileset_2_1.png',
        'Border_wall_left': 'Tileset_1_0.png',
        'Border_wall_right': 'Tileset_1_2.png',
        'Border_wall_top_left_corner': 'Tileset_1_1.png',
        'Border_wall_top_right_corner': 'Tileset_1_1.png',
        'Border_wall_bottom_left_corner': 'Tileset_1_1.png',
        'Border_wall_bottom_right_corner': 'Tileset_1_1.png',
        
        # 凹牆變體
        'Border_wall_concave_top_left': 'Tileset_0_0.png',
        'Border_wall_concave_top_right': 'Tileset_0_2.png',
        'Border_wall_concave_bottom_left': 'Tileset_2_0.png',
        'Border_wall_concave_bottom_right': 'Tileset_2_2.png',
        
        # 凸牆變體
        'Border_wall_convex_top_left': 'Tileset_5_1.png',
        'Border_wall_convex_top_right': 'Tileset_5_0.png',
        'Border_wall_convex_bottom_left': 'Tileset_6_0.png',
        'Border_wall_convex_bottom_right': 'Tileset_6_1.png',
        
        # 樓層瓦片 (新的樓層類型使用 'temp.png')
        'Room_floor': 'Tileset_1_1.png',
        'Lobby_room_floor': 'Tileset_1_1.png', 
        'End_room_floor': 'Tileset_1_1.png',
        'Start_room_floor': 'Tileset_1_1.png',
        'Monster_room_floor': 'Tileset_1_1.png',
        'Trap_room_floor': 'Tileset_1_1.png',
        'Reward_room_floor': 'Tileset_1_1.png',
        'NPC_room_floor': 'Tileset_1_1.png',

        # 環境與結構瓦片
        'Outside': 'Tileset_0_3',
        'Bridge_floor': 'Tileset_1_1.png',
        'Door': 'temp.png',

        # 特殊物件 & 生成點
        'End_room_portal': 'Tileset_1_1.png',
        'Player_spawn': 'Tileset_1_1.png',
        'Monster_spawn': 'Tileset_1_1.png',
        'Trap_spawn': 'Tileset_1_1.png',
        'Reward_spawn': 'Tileset_1_1.png',
        'NPC_spawn': 'Tileset_1_1.png',
        
        # 大廳 NPC/物件
        'Magic_crystal_NPC_spawn': 'Tileset_1_1.png',
        'Dungeon_portal_NPC_spawn': 'Tileset_1_1.png',
        'Alchemy_pot_NPC_spawn': 'Tileset_1_1.png',
        'Dummy_spawn': 'Tileset_1_1.png',
    }
    return load_tileset(config, get_project_path, tile_mapping)

def load_foreground_tileset(config: DungeonConfig, get_project_path) -> Dict[str, pygame.Surface]:
    """載入前景貼圖集 (牆壁)。"""
    # 這裡是您提供的牆壁映射
    tile_mapping = {
    }
    return load_tileset(config, get_project_path, tile_mapping)