from typing import List, Dict, Tuple, Optional
import json
from .entities.player.player import Player
from .config import TILE_SIZE
from .entities.skill.shoot_skill import ShootingSkill
from .entities.skill.buff_skill import BuffSkill
from .entities.skill.abstract_skill import Skill
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
        self.awakened_elements = set()  # Set of awakened element names
        self.amplifiers = {}  # Dict of amplifiers {type: [effects]}
        self.load_from_json()  # Load data from JSON if available

    def awaken_element(self, element: str, cost: int = 1) -> Tuple[bool, str]:
        """Awaken a new element if enough mana is available.

        Args:
            element: The name of the element to awaken.
            cost: Mana cost to awaken the element.
        """
        if self.mana < cost:
            return False, "Not enough mana"
        if element in self.awakened_elements:
            return False, "Element already awakened"
        self.awakened_elements.add(element)
        self.mana -= cost
        self.save_to_json()
        self.apply_elements_to_player()
        print(f"StorageManager: Awakened element {element}, deducted {cost} mana")
        return True, ""
            
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
                self.skills_library = data.get('skills_library', [])  # Directly load skills_library as List[Dict]
                self.awakened_elements = set(data.get('awakened_elements', []))
                self.amplifiers = data.get('amplifiers', {})
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
        """Add a skill dictionary to the skills library."""
        self.skills_library.append(skill_dict)
        self.save_to_json()  # Save to JSON after adding skill
        print(f"StorageManager: Added skill {skill_dict['name']} to library")

    def get_skill_instance(self, name: str) -> Optional[Skill]:
        """Retrieve a skill instance by name from the skills library."""
        for d in self.skills_library:
            if d['name'] == name:
                return self.create_skill_from_dict(d)
        return None

    def get_skills_library(self) -> List[Dict]:
        """Get the skill library.

        Returns:
            List[Dict]: List of all skill data.
        """
        return self.skills_library

    def create_skill_from_dict(self, data: Dict) -> Optional['Skill']:
        """Create a skill instance from a dictionary.

        Args:
            data: Dictionary containing skill data with 'name', 'type', 'element', and 'params'.

        Returns:
            Optional[Skill]: The created skill instance or None if type is unknown.
        """
        name = data.get('name')
        skill_type = data.get('type')
        element = data.get('element', 'untyped')
        params = data.get('params', {})
        energy_cost = params.get('energy_cost', 20.0)

        if skill_type == 'shooting':
            return ShootingSkill(
                name=name,
                element=element,
                energy_cost=energy_cost,
                damage_level=params.get('damage', 0),
                penetration_level=params.get('penetration', 0),
                elebuff_level=params.get('elebuff', 0),
                explosion_level=params.get('explosion', 0),
                speed_level=params.get('speed', 0)
            )
        elif skill_type == 'buff':
            return BuffSkill(
                name=name,
                type=skill_type,
                element=element,
                buff_name=params.get('sub_type', None),
                energy_cost=energy_cost,
                buff_duration_level=params.get('duration', 0),
                element_resistance_level=params.get('element_resistance', 0),
                counter_element_resistance_level=params.get('counter_element_resistance', 0),
                shield_level=params.get('shield', 0),
                remove_element_debuff=params.get('remove_element', 0) > 0,
                remove_counter_element_debuff=params.get('remove_counter', 0) > 0,
                avoid_level=params.get('avoid', 0),
                speed_level=params.get('speed', 0)
            )
        else:
            print(f"StorageManager: Unknown skill type {skill_type}")
            return None

    def apply_stats_to_player(self) -> None:
        """Apply current stat levels to the player."""
        if not self.game.entity_manager.player:
            print("StorageManager: No player instance found")
            return
        player = self.game.entity_manager.player
        # Apply attack level
        player.damage = 10 + self.attack_level * 5  # Example: +5 damage per level
        # Apply defense level
        player.defense = 1 + self.defense_level  # Example: +1 defense per level
        player.max_shield = 5 + self.defense_level ** 2  # Example: +2 shield per level
        # Apply movement level
        player.max_speed = TILE_SIZE * (5 + self.movement_level * 0.2)  # Example: +0.2 speed per level
        player.energy_regen_rate = 5 + self.movement_level * 2  # Example: +1 energy regen per level
        player.max_energy = 100 + self.movement_level * 20  # Example:
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
        player.skill_chain = [[] for _ in range(player.max_skill_chains)]
        player.current_skill_chain_idx = 0
        player.current_skill_idx = 0
        # Add skills to the first skill chain
        for skill_dict in self.skills_library:
            skill = self.create_skill_from_dict(skill_dict)
            if skill:
                player.add_skill_to_chain(skill, chain_idx=0)
        print(f"StorageManager: Applied {len(self.skills_library)} skills to player skill chain")

    def apply_elements_to_player(self) -> None:
        """Apply awakened elements to the player."""
        if not self.game.entity_manager.player:
            print("StorageManager: No player instance found")
            return
        player = self.game.entity_manager.player
        player.elements = self.awakened_elements
        print(f"StorageManager: Applied {len(self.awakened_elements)} awakened elements to player")

    def apply_amplifiers_to_player(self) -> None:
        """Apply amplifiers to the player."""
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