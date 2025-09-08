from typing import List, Dict
from src.entities.character.skills.skill_library import SKILL_LIBRARY
from src.entities.character.weapons.weapon_library import WEAPON_LIBRARY

class StorageManager:
    def __init__(self, game: 'Game'):
        self.game = game
        self.skills_library = SKILL_LIBRARY
        self.weapons_library = WEAPON_LIBRARY

    def get_skills_library(self) -> List[Dict]:
        """Get the skills library."""
        return self.skills_library

    def get_weapons_library(self) -> List[Dict]:
        """Get the weapons library."""
        return self.weapons_library