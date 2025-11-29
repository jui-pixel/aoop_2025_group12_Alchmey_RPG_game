# src/entities/skill/abstract_skill.py
from abc import ABC, abstractmethod
from typing import Tuple

class Skill(ABC):
    def __init__(self, name: str, type: str, element: str, energy_cost: float):
        self.name = name
        self.type = type
        self.element = element
        self.energy_cost = energy_cost
        self.last_used = 0.0

    @abstractmethod
    def activate(self, player: 'Player', game: 'Game', target_position: Tuple[float, float], current_time: float) -> None:
        """Activate the skill, applying its effects."""
        pass