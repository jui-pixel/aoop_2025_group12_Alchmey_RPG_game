from typing import List, Dict, Tuple
import json
from .entities.player.player import Player
from .config import TILE_SIZE
from .entities.skill.skill import create_skill_from_dict

class StorageManager:
    def __init__(self, game: 'Game'):
        """Initialize the storage manager to manage game data (stats, skills, elements, amplifiers).

        Args:
            game: The main game instance for interaction with other modules.
        """
        self.game = game
        self.skills_library = []  # List[Dict] for skill data
        self.mana = 1000  # Default starting mana
        # Initialize stat levels
        self.attack_level = 0
        self.defense_level = 0
        self.movement_level = 0
        self.health_level = 0
        # Initialize skills, awakened elements, and amplifiers
        self.skills = []  # List of skill names or IDs
        self.awakened_elements = set()  # Set of awakened element names
        self.amplifiers = {}  # Dict of amplifiers {type: [effects]}
        self.load_from_json()  # Load data from JSON if available

    def load_from_json(self) -> None:
        """Load game data from a JSON file."""
        try:
            with open('player_data.json', 'r') as file:
                data = json.load(file)
                self.attack_level = data.get('attack_level', 0)
                self.defense_level = data.get('defense_level', 0)
                self.movement_level = data.get('movement_level', 0)
                self.health_level = data.get('health_level', 0)
                self.mana = data.get('mana', 1000)  # Default to 1000 if not in JSON
                self.skills = data.get('skills', [])
                self.awakened_elements = set(data.get('awakened_elements', []))
                self.amplifiers = data.get('amplifiers', {})
                self.skills_library = data.get('skills_library', [])
                print("StorageManager: Loaded data from player_data.json")
                self.apply_all_to_player()  # Apply loaded data to player
        except FileNotFoundError:
            print("StorageManager: No player_data.json found, using default values")
        except json.JSONDecodeError:
            print("StorageManager: Invalid JSON format, using default values")

    def save_to_json(self) -> None:
        """Save game data to a JSON file."""
        data = {
            'attack_level': self.attack_level,
            'defense_level': self.defense_level,
            'movement_level': self.movement_level,
            'health_level': self.health_level,
            'mana': self.mana,
            'skills': self.skills,
            'awakened_elements': list(self.awakened_elements),
            'amplifiers': self.amplifiers,
            'skills_library': self.skills_library
        }
        try:
            with open('player_data.json', 'w') as file:
                json.dump(data, file, indent=4)
                print("StorageManager: Saved data to player_data.json")
        except Exception as e:
            print(f"StorageManager: Failed to save to player_data.json: {e}")

    def add_skill_to_library(self, skill_dict: Dict) -> None:
        self.skills_library.append(skill_dict)

    def get_skill_instance(self, name: str):
        for d in self.skills_library:
            if d['name'] == name:
                return create_skill_from_dict(d)
        return None

    def get_skills_library(self) -> List[Dict]:
        """Get the skill library.

        Returns:
            List[Dict]: List of all skill data.
        """
        return self.skills_library

    def add_skill(self, skill_name: str, cost: int = 200) -> Tuple[bool, str]:
        """Add a skill to the player's skill list if enough mana is available.

        Args:
            skill_name: The name or ID of the skill to add.
            cost: Mana cost to acquire the skill.
        """
        if self.mana < cost:
            return False, "Not enough mana"
        if skill_name in self.skills:
            return False, "Skill already acquired"
        self.skills.append(skill_name)
        self.mana -= cost
        self.save_to_json()
        self.apply_skills_to_player()
        print(f"StorageManager: Added skill {skill_name}, deducted {cost} mana")
        return True, ""

    def apply_stats_to_player(self) -> None:
        """Apply current stat levels to the player."""
        if not self.game.entity_manager.player:
            print("StorageManager: No player instance found")
            return
        player = self.game.entity_manager.player
        # Apply attack level
        # player.damage = 10 + self.attack_level * 5  # Example: +5 damage per level
        # Apply defense level
        player.defense = 1 + self.defense_level  # Example: +1 defense per level
        # Apply movement level
        player.max_speed = TILE_SIZE * (5 + self.movement_level * 0.2)  # Example: +0.2 speed per level
        # Apply health level
        player.base_max_hp = 100 + self.health_level * 20  # Example: +20 HP per level
        player.max_hp = player.base_max_hp  # Update max_hp
        player.current_hp = min(player.current_hp, player.max_hp)  # Ensure current HP doesn't exceed max
        print(f"StorageManager: Applied stats to player - Attack: {player.damage}, Defense: {player.defense}, Speed: {player.max_speed}, HP: {player.max_hp}")
    
    def apply_skills_to_player(self) -> None:
        """Apply current skills to the player."""
        if not self.game.entity_manager.player:
            print("StorageManager: No player instance found")
            return
        player = self.game.entity_manager.player
        # Clear existing skill chains
        player.skill_chain = [[]]
        player.current_skill_chain_idx = 0
        player.current_skill_idx = 0
        # Add skills to the first skill chain
        for skill_name in self.skills:
            skill = self.get_skill_instance(skill_name)
            if skill:
                player.add_skill_to_chain(skill, chain_idx=0)
        print(f"StorageManager: Applied {len(self.skills)} skills to player")

    def apply_elements_to_player(self) -> None:
        """Apply awakened elements to the player."""
        return
        if not self.game.entity_manager.player:
            print("StorageManager: No player instance found")
            return
        player = self.game.entity_manager.player
        player.elements = self.awakened_elements
        print(f"StorageManager: Applied {len(self.awakened_elements)} awakened elements to player")

    def apply_amplifiers_to_player(self) -> None:
        """Apply amplifiers to the player."""
        return
        if not self.game.entity_manager.player:
            print("StorageManager: No player instance found")
            return
        player = self.game.entity_manager.player
        player.amplifiers = self.amplifiers
        print(f"StorageManager: Applied amplifiers to player")

    def apply_all_to_player(self) -> None:
        """Apply all stored data to the player."""
        self.apply_stats_to_player()
        self.apply_skills_to_player()
        self.apply_elements_to_player()
        self.apply_amplifiers_to_player()