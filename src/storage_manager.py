from typing import List, Dict
from .entities.skill.skill_library import SKILL_LIBRARY

class StorageManager:
    def __init__(self, game: 'Game'):
        """初始化儲存管理器，負責管理遊戲中的數據（如技能庫）。

        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.game = game  # 保存遊戲實例引用
        self.skills_library = SKILL_LIBRARY  # 初始化技能庫

    def get_skills_library(self) -> List[Dict]:
        """獲取技能庫。

        Returns:
            List[Dict]: 包含所有技能數據的列表。
        """
        return self.skills_library