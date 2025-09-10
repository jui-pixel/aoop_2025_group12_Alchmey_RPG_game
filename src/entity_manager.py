from typing import List
from src.entities.player.player import Player
from src.entities.npc.alchemy_pot_npc import AlchemyPotNPC
from src.entities.npc.magic_crystal_npc import MagicCrystalNPC
from src.entities.npc.dungeon_portal_npc import DungeonPortalNPC
from src.entities.enemy.dummy import Dummy
from src.entities.bullet.bullet import Bullet
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
import pygame

class EntityManager:
    def __init__(self, game: 'Game'):
        self.game = game
        self.player = None
        self.npc_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.projectile_group = pygame.sprite.Group()

    def initialize_lobby_entities(self, room) -> None:
        """Initialize entities for the lobby room."""
        # 設置玩家在房間中心
        center_x, center_y = self.game.dungeon_manager.get_room_center(room)
        self.player = Player(x=center_x, y=center_y, game=self.game)
        # 初始化 NPC，確保間距足夠避免立即互動
        self.npc_group.empty()
        self.npc_group.add(AlchemyPotNPC(x=center_x - 200, y=center_y, game=self.game))
        self.npc_group.add(MagicCrystalNPC(x=center_x - 100, y=center_y, game=self.game))
        self.npc_group.add(DungeonPortalNPC(x=center_x + 100, y=center_y, game=self.game, 
                                           available_dungeons=[{'name': 'Fire Dungeon', 'level': 1, 'room_id': 1}]))
        self.npc_group.add(Dummy(x=center_x + 200, y=center_y, game=self.game))
        print(f"EntityManager: Initialized player at ({center_x}, {center_y}), {len(self.npc_group)} NPCs")

    def update(self, dt: float, current_time: float) -> None:
        """Update all entities."""
        if self.player:
            self.player.update(dt, current_time)
        self.npc_group.update(dt, current_time)
        self.enemy_group.update(dt, current_time)
        self.projectile_group.update(dt, current_time)

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw all entities."""
        self.npc_group.draw(screen)
        for entity in self.npc_group:
            entity.draw(screen, camera_offset)
        self.enemy_group.draw(screen)
        for entity in self.enemy_group:
            entity.draw(screen, camera_offset)
        self.projectile_group.draw(screen)
        for entity in self.projectile_group:
            entity.draw(screen, camera_offset)
        if self.player:
            self.player.draw(screen, camera_offset)

    def calculate_distance_to(self, entity1, entity2) -> float:
        """Calculate distance between two entities."""
        return ((entity1.x - entity2.x) ** 2 + (entity1.y - entity2.y) ** 2) ** 0.5