from typing import Optional, Dict, List, Tuple
import pygame
from src.entities.basic_entity import BasicEntity
from src.entities.health_entity import HealthEntity
from src.entities.buffable_entity import BuffableEntity, BuffSynthesizer
from src.config import *
from src.utils.elements import ELEMENTS  # Fixed potential typo: ulits -> utils
from src.entities.buff.buff import Buff
from src.entities.buff.element_buff import ELEMENTAL_BUFFS

class AlchemyPotNPC(HealthEntity, BuffableEntity):
    """A stationary NPC for alchemy and item/skill synthesis in the lobby."""
    
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 64, 
                 h: int = 64, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "alchemy_pot_npc",
                 base_max_hp: int = 999999,  # High health, effectively indestructible
                 max_shield: int = 0,
                 dodge_rate: float = 0.0,
                 element: str = "earth",  # Earth element for alchemy theme
                 defense: int = 100,
                 resistances: Optional[Dict[str, float]] = None,
                 invulnerable: bool = True):
        # Initialize HealthEntity first
        HealthEntity.__init__(
            self, x=x, y=y, w=w, h=h, image=image, shape=shape, game=game, tag=tag,
            base_max_hp=base_max_hp, max_shield=max_shield, dodge_rate=dodge_rate,
            element=element, defense=defense, resistances=resistances, invulnerable=invulnerable,
            init_basic=False
        )
        # Initialize BuffableEntity for potential buffs
        BuffableEntity.__init__(self, x=x, y=y, w=w, h=h, image=image, shape=shape, game=game, tag=tag, init_basic=False)
        # Initialize BasicEntity last
        BasicEntity.__init__(self, x=x, y=y, w=w, h=h, image=image, shape=shape, game=game, tag=tag)
        
        self.interaction_range: float = 80.0
        self.alchemy_options: List[Dict] = [
            {'ingredients': ['fire', 'water'], 'result': 'Fog'},
            {'ingredients': ['earth', 'water'], 'result': 'Mud'},
            {'ingredients': ['fire', 'ice'], 'result': 'Vulnerable'},
        ]
        self.is_interacting: bool = False
        self.buff_synthesizer = BuffSynthesizer()

    def calculate_distance_to(self, other_entity):
        """Calculate Euclidean distance to another entity."""
        dx = self.x - other_entity.x
        dy = self.y - other_entity.y
        return (dx**2 + dy**2)**0.5

    def update(self, dt: float, current_time: float) -> None:
        """Update the NPC, check for player interaction."""
        if self.current_hp < self.max_hp:
            self.heal(int(1000 * dt))
        
        # Check for nearby player interaction
        if self.game and self.game.entity_manager.player:
            distance = self.calculate_distance_to(self.game.entity_manager.player)
            if distance <= self.interaction_range and not self.is_interacting:
                self.start_interaction()
            elif distance > self.interaction_range and self.is_interacting:
                self.end_interaction()
        
        BuffableEntity.update(self, dt, current_time)
        super().update(dt, current_time)

    def start_interaction(self) -> None:
        """Initiate alchemy menu via MenuManager."""
        self.is_interacting = True
        if self.game:
            self.game.show_menu('alchemy_menu', self.alchemy_options)
        print("Alchemy Pot NPC: Open alchemy synthesis menu.")

    def end_interaction(self) -> None:
        """End interaction."""
        self.is_interacting = False
        if self.game:
            self.game.hide_menu('alchemy_menu')

    def synthesize_item(self, ingredients: List[str]) -> Optional[str]:
        """Perform alchemy synthesis based on ingredients."""
        for option in self.alchemy_options:
            if sorted(option['ingredients']) == sorted(ingredients):
                result = option['result']
                if self.game and self.game.entity_manager.player:
                    buff = ELEMENTAL_BUFFS.get(result)
                    if buff:
                        self.buff_synthesizer.synthesize_buffs([buff], self.game.entity_manager.player)
                        print(f"Alchemy Pot NPC: Synthesized {result}")
                        return result
        print("Alchemy Pot NPC: Invalid ingredient combination")
        return None

    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                    max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                    lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """NPC takes minimal damage and regenerates."""
        if self.invulnerable:
            return False, 0
        killed, damage = super().take_damage(cause_death=False)
        self.heal(damage)
        return False, damage