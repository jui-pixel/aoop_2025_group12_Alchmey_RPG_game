from typing import Optional, Dict, Tuple, List
import pygame
from src.entities.basic_entity import BasicEntity
from src.entities.health_entity import HealthEntity
from src.entities.buffable_entity import BuffableEntity
from src.entities.buff.buff import Buff
from src.config import *
from src.utils.elements import ELEMENTS  # Fixed typo: ulits -> utils
from src.entities.buff.element_buff import ELEMENTAL_BUFFS

class MagicCrystalNPC(HealthEntity, BuffableEntity):
    """A stationary NPC for magic crystal interactions, buffs, and elemental purchases."""
    
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 64, 
                 h: int = 64, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "magic_crystal_npc",
                 base_max_hp: int = 999999,  # High health
                 max_shield: int = 0,
                 dodge_rate: float = 0.0,
                 element: str = "light",  # Light/magic element
                 defense: int = 100,
                 resistances: Optional[Dict[str, float]] = None,
                 invulnerable: bool = True,
                 available_crystals: Dict[str, Dict] = None):
        # Initialize HealthEntity
        HealthEntity.__init__(
            self, x=x, y=y, w=w, h=h, image=image, shape=shape, game=game, tag=tag,
            base_max_hp=base_max_hp, max_shield=max_shield, dodge_rate=dodge_rate,
            element=element, defense=defense, resistances=resistances, invulnerable=invulnerable,
            init_basic=False
        )
        # Initialize BuffableEntity
        BuffableEntity.__init__(self, x=x, y=y, w=w, h=h, image=image, shape=shape, game=game, tag=tag, init_basic=False)
        # Initialize BasicEntity
        BasicEntity.__init__(self, x=x, y=y, w=w, h=h, image=image, shape=shape, game=game, tag=tag)
        
        self.interaction_range: float = 80.0
        self.available_crystals = available_crystals or {
            elem: {'price': 5, 'buff': ELEMENTAL_BUFFS.get(elem)} for elem in ELEMENTS
        }
        self.is_interacting: bool = False
        self.crystal_glow_timer: float = 0.0

    def calculate_distance_to(self, other_entity):
        """Calculate Euclidean distance to another entity."""
        dx = self.x - other_entity.x
        dy = self.y - other_entity.y
        return (dx**2 + dy**2)**0.5

    def update(self, dt: float, current_time: float) -> None:
        """Update NPC, handle glow animation, interactions."""
        if self.current_hp < self.max_hp:
            self.heal(int(1000 * dt))
        
        # Update crystal glow
        self.crystal_glow_timer += dt
        if self.crystal_glow_timer > 2.0:
            self.crystal_glow_timer = 0.0
        
        # Check player proximity
        if self.game and self.game.entity_manager.player:
            distance = self.calculate_distance_to(self.game.entity_manager.player)
            if distance <= self.interaction_range and not self.is_interacting:
                self.start_interaction()
            elif distance > self.interaction_range and self.is_interacting:
                self.end_interaction()
        
        BuffableEntity.update(self, dt, current_time)
        super().update(dt, current_time)

    def start_interaction(self) -> None:
        """Open crystal shop/menu via MenuManager."""
        self.is_interacting = True
        if self.game:
            self.game.show_menu('crystal_shop', self.available_crystals)
        print("Magic Crystal NPC: Browse elemental crystals and buffs.")

    def end_interaction(self) -> None:
        """Close shop."""
        self.is_interacting = False
        if self.game:
            self.game.hide_menu('crystal_shop')

    def purchase_crystal(self, crystal_type: str) -> bool:
        """Handle crystal purchase and apply buff."""
        if crystal_type in self.available_crystals:
            crystal_info = self.available_crystals[crystal_type]
            player = self.game.entity_manager.player
            if player and hasattr(player, 'gold') and player.gold >= crystal_info['price']:
                player.gold -= crystal_info['price']
                if crystal_info['buff']:
                    player.add_buff(crystal_info['buff'].deepcopy())
                print(f"Magic Crystal NPC: Purchased {crystal_type} crystal.")
                return True
        print("Magic Crystal NPC: Purchase failed.")
        return False

    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                    max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                    lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """Regenerate damage."""
        if self.invulnerable:
            return False, 0
        killed, damage = super().take_damage(cause_death=False)
        self.heal(damage)
        return False, damage