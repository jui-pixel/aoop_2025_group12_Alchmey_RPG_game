from typing import List, Dict
from .entities.skill.skill_library import SKILL_LIBRARY

class StorageManager:
    def __init__(self, game: 'Game'):
        self.game = game
        self.skills_library = SKILL_LIBRARY

    def get_skills_library(self) -> List[Dict]:
        """Get the skills library."""
        return self.skills_library