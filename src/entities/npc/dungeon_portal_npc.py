from typing import Optional, List, Dict, Tuple
import pygame
import math
from src.entities.basic_entity import BasicEntity
from src.entities.health_entity import HealthEntity
from src.entities.buffable_entity import BuffableEntity
from src.config import *

class DungeonPortalNPC(HealthEntity, BuffableEntity):
    """A stationary NPC that handles dungeon entry and teleportation."""
    
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 w: int = 64, 
                 h: int = 64, 
                 image: Optional[pygame.Surface] = None, 
                 shape: str = "rect", 
                 game: 'Game' = None, 
                 tag: str = "dungeon_portal_npc",
                 base_max_hp: int = 999999,  # High health, effectively indestructible
                 max_shield: int = 0,
                 dodge_rate: float = 0.0,
                 element: str = "untyped",  # Neutral for portal
                 defense: int = 100,
                 resistances: Optional[Dict[str, float]] = None,
                 invulnerable: bool = True,
                 available_dungeons: List[Dict] = None):
        # Initialize HealthEntity first
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
            self.image.fill((128, 0, 128))  # 紫色方塊，代表地牢入口
            self.rect = self.image.get_rect(center=(x, y))
        
        self.interaction_range: float = 80.0
        # 確保 available_dungeons 包含 room_id
        self.available_dungeons = available_dungeons or [{'name': 'Fire Dungeon', 'level': 1, 'room_id': 1}]
        for dungeon in self.available_dungeons:
            if 'room_id' not in dungeon:
                dungeon['room_id'] = 1  # 預設值
                print(f"DungeonPortalNPC: Added missing room_id to {dungeon['name']}")
        self.is_interacting: bool = False
        self.show_interact_prompt: bool = False
        self.font = pygame.font.SysFont(None, 24)
        self.portal_effect_active = False

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
        """Show dungeon selection menu via MenuManager."""
        self.is_interacting = True
        if self.game:
            self.game.show_menu('dungeon_menu', self.available_dungeons)
        print(f"DungeonPortalNPC: Opening dungeon menu with {len(self.available_dungeons)} dungeons")

    def end_interaction(self) -> None:
        """Close menu."""
        self.is_interacting = False
        if self.game:
            self.game.hide_menu('dungeon_menu')
        print("DungeonPortalNPC: Closed dungeon menu")

    def enter_dungeon(self, dungeon_name: str) -> bool:
        """Switch to the selected dungeon room."""
        for dungeon in self.available_dungeons:
            if dungeon['name'] == dungeon_name:
                if 'room_id' not in dungeon:
                    print(f"DungeonPortalNPC: Error - No room_id for {dungeon_name}")
                    return False
                if self.game and self.game.entity_manager.player:
                    if dungeon['room_id'] < len(self.game.dungeon_manager.dungeon.rooms):
                        room = self.game.dungeon_manager.dungeon.rooms[dungeon['room_id']]
                        center_x, center_y = self.game.dungeon_manager.get_room_center(room)
                        self.game.entity_manager.player.set_position(center_x, center_y)
                        self.game.dungeon_manager.switch_room(dungeon['room_id'])
                        self.game.event_manager.state = "playing"
                        self.portal_effect_active = True
                        print(f"DungeonPortalNPC: Entered {dungeon_name}, room_id: {dungeon['room_id']}")
                        return True
                    else:
                        print(f"DungeonPortalNPC: Invalid room_id {dungeon['room_id']} for {dungeon_name}")
        print(f"DungeonPortalNPC: Failed to enter {dungeon_name}")
        return False

    def take_damage(self, factor: float = 1.0, element: str = "untyped", base_damage: int = 0, 
                    max_hp_percentage_damage: int = 0, current_hp_percentage_damage: int = 0, 
                    lose_hp_percentage_damage: int = 0, cause_death: bool = True) -> Tuple[bool, int]:
        """Minimal damage, regenerate."""
        if self.invulnerable:
            return False, 0
        killed, damage = super().take_damage(cause_death=False)
        self.heal(damage)
        return False, damage