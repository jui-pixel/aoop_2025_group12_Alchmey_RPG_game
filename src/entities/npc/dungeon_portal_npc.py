from typing import Optional, List, Dict, Tuple
import pygame
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
        
        self.interaction_range: float = 80.0
        self.available_dungeons = available_dungeons or [
            {'name': 'Fire Dungeon', 'level': 1, 'room_id': 1},
            {'name': 'Ice Dungeon', 'level': 2, 'room_id': 2}
        ]
        self.is_interacting: bool = False
        self.portal_effect_active: bool = False
        self.glow_timer: float = 0.0

    def calculate_distance_to(self, other_entity):
        """Calculate Euclidean distance to another entity."""
        dx = self.x - other_entity.x
        dy = self.y - other_entity.y
        return (dx**2 + dy**2)**0.5

    def update(self, dt: float, current_time: float) -> None:
        """Update the NPC, animate portal if active, check interactions."""
        if self.current_hp < self.max_hp:
            self.heal(int(1000 * dt))
        
        # Animate portal glow
        self.glow_timer += dt
        if self.glow_timer > 1.0:
            self.glow_timer = 0.0
            self.portal_effect_active = not self.portal_effect_active
        
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
        """Show dungeon selection menu via MenuManager."""
        self.is_interacting = True
        if self.game:
            self.game.show_menu('dungeon_menu', self.available_dungeons)
        print("Dungeon Portal NPC: Select and enter dungeon.")

    def end_interaction(self) -> None:
        """Close menu."""
        self.is_interacting = False
        if self.game:
            self.game.hide_menu('dungeon_menu')

    def enter_dungeon(self, dungeon_name: str) -> bool:
        """Switch to the selected dungeon room."""
        for dungeon in self.available_dungeons:
            if dungeon['name'] == dungeon_name:
                if self.game and self.game.entity_manager.player:
                    # Ensure room_id exists in dungeon
                    if dungeon['room_id'] < len(self.game.dungeon_manager.dungeon.rooms):
                        room = self.game.dungeon_manager.dungeon.rooms[dungeon['room_id']]
                        center_x, center_y = self.game.dungeon_manager.get_room_center(room)
                        self.game.entity_manager.player.set_position(center_x, center_y)
                        self.game.dungeon_manager.switch_room(dungeon['room_id'])
                        self.game.event_manager.state = "playing"
                        self.portal_effect_active = True
                        print(f"Dungeon Portal NPC: Entered {dungeon_name}")
                        return True
        print(f"Dungeon Portal NPC: Failed to enter {dungeon_name}")
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