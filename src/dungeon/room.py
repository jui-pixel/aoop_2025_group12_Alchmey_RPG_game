# src/dungeon/room.py
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum
import random
# 定義房間類型枚舉，表示地牢中房間的不同功能
class RoomType(Enum):
    EMPTY = "empty"  # 空房間，沒有特殊功能
    START = "start"  # 出生點房間，玩家的起始位置
    MONSTER = "monster"  # 怪物房，包含敵人
    TRAP = "trap"  # 陷阱房，包含危險陷阱
    REWARD = "reward"  # 獎勵房，包含寶藏或道具
    END = "end"  # 終點房間，包含傳送門
    NPC = "npc"  # NPC房間，包含NPC
    LOBBY = "lobby"  # 大廳房間，玩家可以在此選擇技能或武器

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
        if self.tiles is None:
            # 初始化瓦片為空地板
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

        if self.room_type == RoomType.LOBBY:
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
            
            # Calculate number of chests based on room size (1-5)
            floor_area = floor_width * floor_height
            num_chests = max(1, min(5, floor_area // 20))
            
            # Define center area for chest placement (±2 tiles from center)
            center_area = [(r, c) for r in range(center_y - 2, center_y + 3)
                         for c in range(center_x - 2, center_x + 3)
                         if 1 <= r < int(self.height) - 1 and 1 <= c < int(self.width) - 1]
            # Shuffle and select spawn points for chests
            random.shuffle(center_area)
            for i in range(min(num_chests, len(center_area))):
                row, col = center_area[i]
                self.tiles[row][col] = 'Reward_spawn'
            print(f"Reward Room (ID: {self.id}) with {num_chests} chests placed.")
                
        elif self.room_type == RoomType.NPC:
            for row in range(int(self.height)):
                for col in range(int(self.width)):
                    self.tiles[row][col] = 'NPC_room_floor'
            self.tiles[center_y][center_x] = 'NPC_spawn'
            print(f"NPC Room (ID: {self.id}) NPC placed.")
        # 未來可為其他房間類型（如 MONSTER、TRAP、REWARD）添加特殊瓦片邏輯

    def get_tiles(self) -> List[List[str]]:
        """返回房間的瓦片陣列"""
        return self.tiles
    
    @property
    def is_end_room(self) -> bool:
        """檢查房間是否為終點房間，向後相容"""
        return self.room_type == RoomType.END