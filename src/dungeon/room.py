# src/dungeon/room.py
from typing import List, Tuple
from dataclasses import dataclass
from src.dungeon.config.dungeon_config import RoomType
import random


# 定義房間數據結構，用於儲存房間的屬性和瓦片數據
@dataclass
class Room:
    # 房間類，用來表示地牢中的單個房間，包含位置、尺寸、瓦片和類型等資訊
    id: int   # 房間的唯一標識符，每個房間有獨一無二的 ID
    x: float  # 房間左上角的 x 座標（瓦片單位）
    y: float  # 房間左上角的 y 座標（瓦片單位）
    width: float  # 房間的寬度（以瓦片數為單位）
    height: float  # 房間的高度（以瓦片數為單位）
    tiles: List[List[str]] = None # 房間的瓦片陣列，儲存每個瓦片的類型（例如 'Room_floor'、'End_room_portal'）
    room_type: RoomType = RoomType.EMPTY  # 房間的類型，預設為空房間
    connections: List[Tuple[int, str]] = None  # 房間連接到其他房間的列表，包含目標房間 ID 和方向（預設為 None）

    def __post_init__(self):
        # 初始化後處理，確保 connections 為空列表
        if self.connections is None:
            self.connections = []
        # 根據房間類型設置瓦片
        self.generate_tiles()
    
    def generate_tiles(self) -> None:
        """Configure tiles based on room type with optimized item placement"""
        print(f"Generating tiles for Room ID {self.id} of type {self.room_type}")
        # 初始化所有瓦片為基本地板
        self.tiles = [['Room_floor' for _ in range(int(self.width))] 
                          for _ in range(int(self.height))]
        
        # Calculate usable floor area (excluding walls)
        floor_width = int(self.width) - 2
        floor_height = int(self.height) - 2
        center_x = int(self.width) // 2
        center_y = int(self.height) // 2

        if self.room_type == RoomType.END:
            for row in range(1, int(self.height) - 1):
                for col in range(1, int(self.width) - 1):
                    self.tiles[row][col] = 'End_room_floor'
            self.tiles[center_y][center_x] = 'End_room_portal'
            print(f"End Room (ID: {self.id}) Portal placed.")

        elif self.room_type == RoomType.START:
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'Start_room_floor'
            self.tiles[center_y][center_x] = 'Player_spawn'
            print(f"Start Room (ID: {self.id}) Player spawn placed.")

        elif self.room_type == RoomType.LOBBY:
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'Lobby_room_floor'
            
            center_x = int(self.width / 2)
            center_y = int(self.height / 2)
            
            # 靠近中心放置 NPC
            self.tiles[3][4] = 'Magic_crystal_NPC_spawn'  # 左上
            self.tiles[3][int(self.width) - 4] = 'Dungeon_portal_NPC_spawn'  # 右上
            self.tiles[int(self.height) - 3][4] = 'Alchemy_pot_NPC_spawn'  # 左下
            self.tiles[int(self.height) - 3][int(self.width) - 4] = 'Dummy_spawn'  # 右下
            self.tiles[center_y + 3][center_x] = 'Player_spawn'  # 中心下
            self.tiles[center_y - 3][center_x] = 'NPC_spawn'  # 中心 NPC
            print(f"Lobby Room (ID: {self.id}) NPC and Player spawns placed.")

        elif self.room_type == RoomType.MONSTER:
            # Monster room: Scale number of monsters based on room size
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'Monster_room_floor'
            
            # Calculate number of monsters (1 monster per ~72 tiles, min 1, max 15)
            floor_area = floor_width * floor_height
            num_monsters = max(1, min(15, floor_area // 72))
            
            # Define available spawn points (excluding walls)
            spawn_points = [(r, c) for r in range(1, int(self.height) - 1)
                          for c in range(1, int(self.width) - 1)]
            # Shuffle and select spawn points
            random.shuffle(spawn_points)
            for i in range(min(num_monsters, len(spawn_points))):
                row, col = spawn_points[i]
                self.tiles[row][col] = 'Monster_spawn'
            print(f"Monster Room (ID: {self.id}) with {num_monsters} monsters placed.")

        elif self.room_type == RoomType.TRAP:
            # Trap room: Random trap placement with NPC in center
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'Trap_room_floor'
            
            # Place NPC in center
            self.tiles[center_y][center_x] = 'NPC_spawn'
            
            # Calculate number of traps (1 trap per ~16 tiles, min 1, max 50)
            floor_area = floor_width * floor_height
            num_traps = max(1, min(50, floor_area // 16))
            
            # Define available spawn points (excluding walls and NPC)
            spawn_points = [(r, c) for r in range(1, int(self.height) - 1)
                          for c in range(1, int(self.width) - 1)
                          if (r, c) != (center_y, center_x)]
            # Shuffle and select spawn points for traps
            random.shuffle(spawn_points)
            for i in range(min(num_traps, len(spawn_points))):
                row, col = spawn_points[i]
                self.tiles[row][col] = 'Trap_spawn'
            print(f"Trap Room (ID: {self.id}) with {num_traps} traps placed.")

        elif self.room_type == RoomType.REWARD:
            # Reward room: Place 1-5 treasure chests in center area
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'Reward_room_floor'
            
            
            self.tiles[center_y][center_x] = 'Reward_spawn'
            
            print(f"Reward Room (ID: {self.id}) with chests placed.")
                
        elif self.room_type == RoomType.BOSS:
            # Boss Room: Center spawning for boss, specialized floor
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'Boss_room_floor'
            
            # Spawn Boss in the center
            self.tiles[center_y][center_x] = 'Boss_spawn'
            
            # Spawn Player near the center
            self.tiles[center_y + 3][center_x] = 'Player_spawn'
            print(f"Boss Room (ID: {self.id}) Boss spawn placed.")

        elif self.room_type == RoomType.FINAL:
            # Final Room: Center NPC, surrounded by chests
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'Final_room_floor'
            
            # Spawn Final NPC (Win condition)
            self.tiles[center_y][center_x] = 'Final_NPC_spawn'
            
            # Spawn Player near the center
            self.tiles[center_y + 3][center_x] = 'Player_spawn'
            
            # Place chests around the center
            chest_offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
            for dr, dc in chest_offsets:
                r, c = center_y + dr, center_x + dc
                if 1 <= r < int(self.height) - 1 and 1 <= c < int(self.width) - 1:
                    self.tiles[r][c] = 'Reward_spawn'
            
            print(f"Final Room (ID: {self.id}) Final NPC and chests placed.")

        elif self.room_type == RoomType.NPC:
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'NPC_room_floor'
            self.tiles[center_y][center_x] = 'NPC_spawn'
            print(f"NPC Room (ID: {self.id}) NPC placed.")
        # 未來可為其他房間類型（如 MONSTER、TRAP、REWARD）添加特殊瓦片邏輯
        elif self.room_type == RoomType.EMPTY: pass
        
        else:
            raise NotImplementedError(f"Tile generation not implemented for room type: {self.room_type}")
        
        
    def get_tiles(self) -> List[List[str]]:
        """返回房間的瓦片陣列"""
        return self.tiles
    
    @property
    def is_end_room(self) -> bool:
        """檢查房間是否為終點房間，向後相容"""
        return self.room_type == RoomType.END