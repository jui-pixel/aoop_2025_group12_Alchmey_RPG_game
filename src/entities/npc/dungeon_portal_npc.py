from typing import Optional, List, Dict, Tuple
import pygame
import math
from src.entities.basic_entity import BasicEntity
from src.entities.health_entity import HealthEntity
from src.entities.buffable_entity import BuffableEntity
from src.entities.enemy.dummy import Dummy
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
            self.image.fill((128, 0, 128))  # Purple square for dungeon portal
            self.rect = self.image.get_rect(center=(x, y))
        
        self.interaction_range: float = 80.0
        self.available_dungeons = available_dungeons or [{'name': 'Test Dungeon', 'level': 1, 'dungeon_id': 1}]
        for dungeon in self.available_dungeons:
            if 'dungeon_id' not in dungeon:
                dungeon['dungeon_id'] = 1
                print(f"DungeonPortalNPC: Added missing dungeon_id to {dungeon['name']}")
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

    def _is_tile_passable(self, tile_x: int, tile_y: int, dungeon: 'Dungeon') -> bool:
        """Check if a tile is passable."""
        if 0 <= tile_y < dungeon.grid_height and 0 <= tile_x < dungeon.grid_width:
            return dungeon.dungeon_tiles[tile_y][tile_x] in PASSABLE_TILES
        return False

    def _has_adjacent_passable_tile(self, tile_x: int, tile_y: int, dungeon: 'Dungeon') -> bool:
        """Check if a tile has at least one adjacent passable tile."""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Down, Up, Right, Left
        for dx, dy in directions:
            adj_x, adj_y = tile_x + dx, tile_y + dy
            if self._is_tile_passable(adj_x, adj_y, dungeon):
                return True
        return False

    def enter_dungeon(self, dungeon_name: str) -> bool:
        """Switch to the selected dungeon room, initialize dungeon, and place entities."""
        for dungeon in self.available_dungeons:
            if dungeon['name'] == dungeon_name:
                if 'dungeon_id' not in dungeon:
                    print(f"DungeonPortalNPC: Error - No dungeon_id for {dungeon_name}")
                    return False
                # Initialize full dungeon if not already initialized
                print("DungeonPortalNPC: Initializing full dungeon")
                self.game.dungeon_manager.dungeon.initialize_dungeon()  # Assumes this method exists
                if self.game and self.game.entity_manager.player:

                    # Reset player displacement to prevent stuck movement
                    self.game.entity_manager.player.displacement = (0, 0)
                    self.game.entity_manager.initialize_dungeon_entities()  # Initialize entities in the dungeon
                    self.game.event_manager.state = "playing"
                    # Explicitly hide the dungeon menu to ensure menu is closed
                    self.game.hide_menu('dungeon_menu')
                    self.game.menu_manager.set_menu(None)
                    self.portal_effect_active = True
                    print(f"DungeonPortalNPC: Entered {dungeon_name}, dungeon_id: {dungeon['dungeon_id']}, menu closed")
                    return True
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
    
    def calculate_distance_to(self, other_entity) -> float:
        """Calculate the Euclidean distance to another entity."""
        dx = self.x - other_entity.x
        dy = self.y - other_entity.y
        return math.sqrt(dx**2 + dy**2)