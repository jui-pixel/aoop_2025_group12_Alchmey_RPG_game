# src/skills/skill.py
from dataclasses import dataclass
from typing import Optional, Callable
# from src.character.player import Player


@dataclass
class Skill:
    name: str
    cooldown: float  # 冷卻時間（秒），0 表示無冷卻
    duration: float  # 效果持續時間（秒），0 表示即時效果
    effect: Callable[['Player', 'Game'], None]  # 技能效果，接受 Player 和 Game 參數
    last_used: float = 0.0  # 上次使用時間
    effect_end_time: float = 0.0  # 效果結束時間（用於持續效果）

    def can_use(self, player: 'Player', current_time: float) -> bool:
        """檢查技能是否可用"""
        if self.cooldown == 0:
            return True
        return (current_time - self.last_used) >= self.cooldown

    def use(self, player: 'Player', game: 'Game', current_time: float) -> bool:
        """使用技能，調用效果並更新冷卻和持續時間"""
        if not self.can_use(player, current_time):
            return False
        try:
            self.effect(player, game)
            if self.cooldown > 0:
                self.last_used = current_time
            if self.duration > 0:
                self.effect_end_time = current_time + self.duration
            return True
        except Exception as e:
            print(f"Skill {self.name} effect failed: {e}")
            return False

    def is_effect_active(self, current_time: float) -> bool:
        """檢查技能效果是否仍在持續"""
        return self.duration > 0 and current_time < self.effect_end_time