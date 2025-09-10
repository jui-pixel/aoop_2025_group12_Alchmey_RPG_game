import pygame
from typing import Optional, List, Dict
from src.entities.player.player import Player
from src.entities.enemy.enemy1 import Enemy1
from src.entities.enemy.dummy import Dummy
from src.entities.npc.alchemy_pot_npc import AlchemyPotNPC
from src.entities.npc.dungeon_portal_npc import DungeonPortalNPC
from src.entities.npc.magic_crystal_npc import MagicCrystalNPC
from src.entities.damage_text import DamageText
from src.config import TILE_SIZE, ROOM_FLOOR_COLORS
from src.utils.elements import ELEMENTS

class EntityManager:
    def __init__(self, game: 'Game'):
        self.game = game
        self.player = None
        self.player_bullet_group = pygame.sprite.Group()
        self.enemy_bullet_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.npc_group = pygame.sprite.Group()
        self.damage_text_group = pygame.sprite.Group()
        self.reward_group = pygame.sprite.Group()
        self.trap_group = pygame.sprite.Group()
        self.environment_group = pygame.sprite.Group()

    def initialize_lobby_entities(self, room) -> None:
        """Initialize player, dummy, and NPCs in the lobby at their designated spawn points."""
        for row in range(int(room.height)):
            for col in range(int(room.width)):
                tile = room.tiles[row][col]
                x = (room.x + col) * TILE_SIZE + TILE_SIZE / 2
                y = (room.y + row) * TILE_SIZE + TILE_SIZE / 2

                if tile == 'Player_spawn':
                    self.player = Player(
                        x=x, y=y, game=self.game, base_max_hp=100, max_speed=10 * TILE_SIZE, 
                        element="untyped", defense=10, resistances=None, damage_to_element=None,
                        can_move=True, can_attack=True, invulnerable=False
                    )
                elif tile == 'Dummy_spawn':
                    dummy = Dummy(
                        x=x, y=y, game=self.game, tag="dummy",
                        base_max_hp=999999999, max_shield=0, dodge_rate=0.0,
                        element="untyped", defense=0, invulnerable=True
                    )
                    self.npc_group.add(dummy)
                elif tile == 'Alchemy_pot_NPC_spawn':
                    alchemy_npc = AlchemyPotNPC(
                        x=x, y=y, game=self.game, tag="alchemy_pot_npc",
                        base_max_hp=999999, max_shield=0, dodge_rate=0.0,
                        element="earth", defense=100, invulnerable=True
                    )
                    self.npc_group.add(alchemy_npc)
                elif tile == 'Dungeon_portal_NPC_spawn':
                    dungeon_npc = DungeonPortalNPC(
                        x=x, y=y, game=self.game, tag="dungeon_portal_npc",
                        base_max_hp=999999, max_shield=0, dodge_rate=0.0,
                        element="untyped", defense=100, invulnerable=True,
                        available_dungeons=[{'name': 'Fire Dungeon', 'level': 1, 'entry_point': (100, 100)}]
                    )
                    self.npc_group.add(dungeon_npc)
                elif tile == 'Magic_crystal_NPC_spawn':
                    crystal_npc = MagicCrystalNPC(
                        x=x, y=y, game=self.game, tag="magic_crystal_npc",
                        base_max_hp=999999, max_shield=0, dodge_rate=0.0,
                        element="light", defense=100, invulnerable=True,
                        available_crystals={elem: {'price': 5, 'buff': None} for elem in ELEMENTS}
                    )
                    self.npc_group.add(crystal_npc)

    def update(self, dt: float, current_time: float) -> None:
        """Update all entities."""
        if self.player:
            self.player.update(dt, current_time)
        self.player_bullet_group.update(dt, current_time)
        self.enemy_bullet_group.update(dt, current_time)
        self.enemy_group.update(dt, current_time)
        self.npc_group.update(dt, current_time)
        self.damage_text_group.update(dt, current_time)
        self.reward_group.update(dt, current_time)
        self.trap_group.update(dt, current_time)
        self.environment_group.update(dt, current_time)

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """Draw all entities."""
        if self.player:
            self.player.draw(screen, camera_offset)
        self.player_bullet_group.draw(screen)
        self.enemy_bullet_group.draw(screen)
        self.enemy_group.draw(screen)
        self.npc_group.draw(screen)
        self.damage_text_group.draw(screen)
        self.reward_group.draw(screen)
        self.trap_group.draw(screen)
        self.environment_group.draw(screen)