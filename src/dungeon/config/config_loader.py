# src/dungeon/config/config_loader.py
"""
配置載入器模組
負責從 JSON 文件載入關卡配置
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .level_config import LevelConfig, MonsterConfig, MonsterPoolConfig


class LevelConfigLoader:
    """
    關卡配置載入器
    
    從 JSON 文件載入關卡配置並轉換為 LevelConfig 物件
    """
    
    def __init__(self, config_dir: str = "levels"):
        """
        初始化配置載入器
        
        Args:
            config_dir: 配置文件目錄路徑（相對於專案根目錄）
        """
        self.config_dir = Path(config_dir)
        
    def load_level(self, level_id: int) -> Optional[LevelConfig]:
        """
        載入指定關卡的配置
        
        Args:
            level_id: 關卡 ID
            
        Returns:
            關卡配置物件，如果載入失敗則返回 None
        """
        config_path = self.config_dir / f"level_{level_id}.json"
        
        if not config_path.exists():
            print(f"警告: 找不到關卡 {level_id} 的配置文件: {config_path}")
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            level_config = self._parse_level_config(data)
            
            # 驗證配置
            is_valid, error = level_config.validate()
            if not is_valid:
                print(f"錯誤: 關卡 {level_id} 配置無效: {error}")
                return None
            
            print(f"成功載入關卡 {level_id} 配置: {level_config.level_name}")
            return level_config
            
        except json.JSONDecodeError as e:
            print(f"錯誤: 無法解析 JSON 文件 {config_path}: {e}")
            return None
        except Exception as e:
            print(f"錯誤: 載入關卡 {level_id} 配置時發生錯誤: {e}")
            return None
    
    def load_level_from_file(self, file_path: str) -> Optional[LevelConfig]:
        """
        從指定文件載入關卡配置
        
        Args:
            file_path: 配置文件的完整路徑
            
        Returns:
            關卡配置物件，如果載入失敗則返回 None
        """
        path = Path(file_path)
        
        if not path.exists():
            print(f"警告: 找不到配置文件: {file_path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            level_config = self._parse_level_config(data)
            
            # 驗證配置
            is_valid, error = level_config.validate()
            if not is_valid:
                print(f"錯誤: 配置文件 {file_path} 無效: {error}")
                return None
            
            print(f"成功載入配置文件: {file_path}")
            return level_config
            
        except json.JSONDecodeError as e:
            print(f"錯誤: 無法解析 JSON 文件 {file_path}: {e}")
            return None
        except Exception as e:
            print(f"錯誤: 載入配置文件 {file_path} 時發生錯誤: {e}")
            return None
    
    def _parse_level_config(self, data: Dict[str, Any]) -> LevelConfig:
        """
        解析 JSON 資料為 LevelConfig 物件
        
        Args:
            data: JSON 資料字典
            
        Returns:
            LevelConfig 物件
        """
        # 解析基本資訊
        level_id = data.get("level_id", 0)
        level_name = data.get("level_name", f"Level {level_id}")
        
        # 解析地牢配置
        dungeon_config = data.get("dungeon_config", {})
        
        # 解析怪物配置
        monster_config_data = data.get("monster_config", {})
        monster_pool = self._parse_monster_pool(monster_config_data)
        
        # 創建 LevelConfig 物件
        return LevelConfig(
            level_id=level_id,
            level_name=level_name,
            grid_width=dungeon_config.get("grid_width", 120),
            grid_height=dungeon_config.get("grid_height", 100),
            max_split_depth=dungeon_config.get("max_split_depth", 6),
            min_room_size=dungeon_config.get("min_room_size", 13),
            room_gap=dungeon_config.get("room_gap", 2),
            extra_bridge_ratio=dungeon_config.get("extra_bridge_ratio", 0.1),
            monster_room_ratio=dungeon_config.get("monster_room_ratio", 0.7),
            trap_room_ratio=dungeon_config.get("trap_room_ratio", 0.15),
            reward_room_ratio=dungeon_config.get("reward_room_ratio", 0.15),
            min_bridge_width=dungeon_config.get("min_bridge_width", 2),
            max_bridge_width=dungeon_config.get("max_bridge_width", 4),
            bias_ratio=dungeon_config.get("bias_ratio", 0.8),
            bias_strength=dungeon_config.get("bias_strength", 0.3),
            monster_pool=monster_pool,
        )
    
    def _parse_monster_pool(self, data: Dict[str, Any]) -> MonsterPoolConfig:
        """
        解析怪物池配置
        
        Args:
            data: 怪物配置資料字典
            
        Returns:
            MonsterPoolConfig 物件
        """
        monsters_data = data.get("monsters", [])
        total_monster_multiplier = data.get("total_monster_multiplier", 1.0)
        
        monsters = []
        for monster_data in monsters_data:
            monster = MonsterConfig(
                type=monster_data.get("type", "unknown"),
                min_count=monster_data.get("min_count", 1),
                max_count=monster_data.get("max_count", 3),
                health_multiplier=monster_data.get("health_multiplier", 1.0),
                damage_multiplier=monster_data.get("damage_multiplier", 1.0),
                spawn_weight=monster_data.get("spawn_weight", 1.0),
            )
            monsters.append(monster)
        
        return MonsterPoolConfig(
            monsters=monsters,
            total_monster_multiplier=total_monster_multiplier,
        )
    
    def save_level(self, level_config: LevelConfig, level_id: Optional[int] = None) -> bool:
        """
        保存關卡配置到 JSON 文件
        
        Args:
            level_config: 要保存的關卡配置
            level_id: 關卡 ID（如果為 None，使用 level_config.level_id）
            
        Returns:
            是否保存成功
        """
        if level_id is None:
            level_id = level_config.level_id
        
        # 確保配置目錄存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = self.config_dir / f"level_{level_id}.json"
        
        try:
            # 驗證配置
            is_valid, error = level_config.validate()
            if not is_valid:
                print(f"錯誤: 無法保存無效的配置: {error}")
                return False
            
            # 轉換為字典並保存
            data = level_config.to_dict()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"成功保存關卡 {level_id} 配置到: {config_path}")
            return True
            
        except Exception as e:
            print(f"錯誤: 保存關卡 {level_id} 配置時發生錯誤: {e}")
            return False
    
    def list_available_levels(self) -> list[int]:
        """
        列出所有可用的關卡 ID
        
        Returns:
            可用的關卡 ID 列表
        """
        if not self.config_dir.exists():
            return []
        
        level_ids = []
        for file_path in self.config_dir.glob("level_*.json"):
            try:
                # 從文件名提取關卡 ID
                level_id = int(file_path.stem.split("_")[1])
                level_ids.append(level_id)
            except (ValueError, IndexError):
                continue
        
        return sorted(level_ids)


def create_default_level_config(level_id: int) -> LevelConfig:
    """
    創建默認的關卡配置
    
    Args:
        level_id: 關卡 ID
        
    Returns:
        默認的 LevelConfig 物件
    """
    # 根據關卡 ID 調整難度
    difficulty_multiplier = 1.0 + (level_id - 1) * 0.2
    
    # 基礎怪物配置
    monsters = [
        MonsterConfig(
            type="slime",
            min_count=1,
            max_count=2,
            health_multiplier=0.8 * difficulty_multiplier,
            damage_multiplier=0.8 * difficulty_multiplier,
            spawn_weight=0.4,
        ),
        MonsterConfig(
            type="goblin",
            min_count=1,
            max_count=3,
            health_multiplier=1.0 * difficulty_multiplier,
            damage_multiplier=1.0 * difficulty_multiplier,
            spawn_weight=0.6,
        ),
    ]
    
    # 高等級添加更多怪物類型
    if level_id >= 3:
        monsters.append(MonsterConfig(
            type="orc",
            min_count=1,
            max_count=2,
            health_multiplier=1.5 * difficulty_multiplier,
            damage_multiplier=1.3 * difficulty_multiplier,
            spawn_weight=0.3,
        ))
    
    if level_id >= 5:
        monsters.append(MonsterConfig(
            type="skeleton",
            min_count=2,
            max_count=4,
            health_multiplier=1.2 * difficulty_multiplier,
            damage_multiplier=1.4 * difficulty_multiplier,
            spawn_weight=0.4,
        ))
    
    monster_pool = MonsterPoolConfig(
        monsters=monsters,
        total_monster_multiplier=difficulty_multiplier,
    )
    
    # 根據關卡調整地牢大小
    base_width = 80 + (level_id - 1) * 20
    base_height = 60 + (level_id - 1) * 15
    
    return LevelConfig(
        level_id=level_id,
        level_name=f"關卡 {level_id}",
        grid_width=min(base_width, 200),
        grid_height=min(base_height, 150),
        max_split_depth=min(4 + level_id, 8),
        min_room_size=13,
        room_gap=2,
        extra_bridge_ratio=0.1 + level_id * 0.02,
        monster_room_ratio=0.7,
        trap_room_ratio=0.15,
        reward_room_ratio=0.15,
        min_bridge_width=2,
        max_bridge_width=4,
        bias_ratio=0.8,
        bias_strength=0.3,
        monster_pool=monster_pool,
    )
