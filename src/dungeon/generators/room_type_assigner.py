# src/dungeon/generators/room_type_assigner.py
"""
房間類型分配器模塊
負責為房間分配類型
"""
import random
from typing import List
from ..room import Room, RoomType
from ..config.dungeon_config import DungeonConfig


class RoomTypeAssigner:
    """
    房間類型分配器
    
    根據配置的比例為房間分配類型，
    確保特殊房間（起始、終點等）正確分配。
    """
    
    def __init__(self, config: DungeonConfig):
        """
        初始化房間類型分配器
        
        Args:
            config: 地牢配置
        """
        self.config = config
    
    def assign_types(self, rooms: List[Room]) -> None:
        """
        為房間分配類型
        
        Args:
            rooms: 房間列表
        """
        if not rooms:
            return
        
        # 1. 分配特殊房間
        self._assign_special_rooms(rooms)
        
        # 2. 分配普通房間
        self._assign_regular_rooms(rooms)
    
    def _assign_special_rooms(self, rooms: List[Room]) -> None:
        """
        分配特殊房間（起始、終點等）
        
        Args:
            rooms: 房間列表
        """
        if len(rooms) < 2:
            return
        
        # 隨機選擇起始房間和終點房間
        available_rooms = rooms.copy()
        
        # 起始房間
        start_room = random.choice(available_rooms)
        start_room.room_type = RoomType.START
        available_rooms.remove(start_room)
        
        # 終點房間（盡量遠離起始房間）
        end_room = self._select_farthest_room(start_room, available_rooms)
        end_room.room_type = RoomType.END
        available_rooms.remove(end_room)
        
        # 如果還有足夠的房間，分配其他特殊房間
        if len(available_rooms) >= 3:
            # NPC 房間
            npc_room = random.choice(available_rooms)
            npc_room.room_type = RoomType.NPC
            available_rooms.remove(npc_room)
    
    def _assign_regular_rooms(self, rooms: List[Room]) -> None:
        """
        按比例分配普通房間類型
        
        Args:
            rooms: 房間列表
        """
        # 找出未分配類型的房間
        unassigned_rooms = [r for r in rooms if r.room_type == RoomType.EMPTY]
        
        if not unassigned_rooms:
            return
        
        # 計算各類型房間數量
        total = len(unassigned_rooms)
        num_monster = int(total * self.config.monster_room_ratio)
        num_trap = int(total * self.config.trap_room_ratio)
        num_reward = total - num_monster - num_trap  # 剩餘的都是獎勵房間
        
        # 打亂房間順序
        random.shuffle(unassigned_rooms)
        
        # 分配類型
        idx = 0
        
        # 怪物房間
        for _ in range(num_monster):
            if idx < len(unassigned_rooms):
                unassigned_rooms[idx].room_type = RoomType.MONSTER
                idx += 1
        
        # 陷阱房間
        for _ in range(num_trap):
            if idx < len(unassigned_rooms):
                unassigned_rooms[idx].room_type = RoomType.TRAP
                idx += 1
        
        # 獎勵房間
        for _ in range(num_reward):
            if idx < len(unassigned_rooms):
                unassigned_rooms[idx].room_type = RoomType.REWARD
                idx += 1
    
    def _select_farthest_room(self, reference: Room, candidates: List[Room]) -> Room:
        """
        選擇距離參考房間最遠的房間
        
        Args:
            reference: 參考房間
            candidates: 候選房間列表
        
        Returns:
            最遠的房間
        """
        if not candidates:
            return reference
        
        ref_cx = reference.x + reference.width / 2
        ref_cy = reference.y + reference.height / 2
        
        max_distance = -1
        farthest_room = candidates[0]
        
        for room in candidates:
            cx = room.x + room.width / 2
            cy = room.y + room.height / 2
            distance = ((cx - ref_cx) ** 2 + (cy - ref_cy) ** 2) ** 0.5
            
            if distance > max_distance:
                max_distance = distance
                farthest_room = room
        
        return farthest_room
    
    def get_room_type_counts(self, rooms: List[Room]) -> dict:
        """
        統計各類型房間的數量
        
        Args:
            rooms: 房間列表
        
        Returns:
            類型到數量的映射
        """
        counts = {}
        for room in rooms:
            room_type = room.room_type
            counts[room_type] = counts.get(room_type, 0) + 1
        return counts
