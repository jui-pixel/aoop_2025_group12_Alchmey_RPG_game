from typing import Optional, Dict, Tuple, List
import pygame
import math
from src.entities.basic_entity import BasicEntity
from src.entities.health_entity import HealthEntity
from src.entities.buffable_entity import BuffableEntity
from src.entities.buff.buff import Buff
from src.config import *
from src.utils.elements import ELEMENTS
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
        
        if self.image is None:
            self.image = pygame.Surface((w, h))
            self.image.fill((255, 255, 255))  # 白色方塊，代表魔法水晶
            self.rect = self.image.get_rect(center=(x, y))
        
        self.interaction_range: float = 80.0
        self.available_crystals = available_crystals or {elem: {'price': 5, 'buff': None} for elem in ELEMENTS}
        self.is_interacting: bool = False
        self.show_interact_prompt: bool = False  # 新增：是否顯示提示
        self.font = pygame.font.SysFont(None, 24)  # 用於提示文字

    def update(self, dt: float, current_time: float) -> None:
        """Update NPC state, check player proximity for interaction prompt."""
        if self.game and self.game.entity_manager.player:
            distance = self.calculate_distance_to(self.game.entity_manager.player)
            self.show_interact_prompt = distance <= self.interaction_range
        BuffableEntity.update(self, dt, current_time)
        super().update(dt, current_time)

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw NPC and interaction prompt if within range."""
        super().draw(screen, camera_offset)
        if self.show_interact_prompt:
            screen_x = self.x - camera_offset[0] - self.w // 2
            screen_y = self.y - camera_offset[1] - self.h // 2 - 20
            prompt_text = self.font.render("Press E to interact", True, (255, 255, 255))
            screen.blit(prompt_text, (screen_x - prompt_text.get_width() // 2 + self.w // 2, screen_y))

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
    
    def calculate_distance_to(self, other_entity) -> float:
        """Calculate the Euclidean distance to another entity."""
        dx = self.x - other_entity.x
        dy = self.y - other_entity.y
        return math.sqrt(dx**2 + dy**2)