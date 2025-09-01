import pygame
import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from src.entities.character.weapons.weapon import *
from src.entities.character.weapons.weapon_library import WEAPON_LIBRARY
from src.entities.character.skills.skill import *
from src.entities.character.skills.skill_library import SKILL_LIBRARY
from src.dungeon.dungeon import *
from src.config import *
from src.entities.character.character import *
from src.entities.enemy.basic_enemy import BasicEnemy
from src.entities.buff import Buff
from src.entities.NPC import NPC
from src.entities.damage_text import DamageText


class Game:
    def __init__(self, screen, pygame_clock):
        """Initialize the game with core components and state."""
        self.screen = screen
        self.clock = pygame_clock
        self.dungeon = Dungeon()
        self.dungeon.game = self
        self.player = None
        self.player_bullet_group = pygame.sprite.Group()
        self.enemy_bullet_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.npc_group = pygame.sprite.Group()
        self.damage_text_group = pygame.sprite.Group()
        self.reward_group = pygame.sprite.Group()
        self.trap_group = pygame.sprite.Group()
        self.environment_group = pygame.sprite.Group()
        self.current_time = 0.0
        self.state = "menu"
        self.selected_skill = None
        self.selected_skills = []
        self.selected_weapons = []
        self.menu_options = ["Enter Lobby", "Exit"]
        self.selected_menu_option = 0
        self.npc_menu_options = ["Select Skills", "Select Weapons", "Start Game"]
        self.selected_npc_menu_option = 0
        self.skills_library = SKILL_LIBRARY
        self.weapons_library = WEAPON_LIBRARY
        self.camera_offset = [0, 0]
        self.camera_lerp_factor = 1.5
        self.original_camera_lerp_factor = 1.5
        self.current_room_id = 0
        self.time_scale = 1.0
        self.minimap_scale = 1
        self.minimap_width = int(self.dungeon.grid_width * self.minimap_scale)
        self.minimap_height = int(self.dungeon.grid_height * self.minimap_scale)
        self.minimap_offset = (SCREEN_WIDTH - self.minimap_width - 10, 10)
        self.fog_map = None
        self.fog_surface = None
        self.last_player_pos = None
        self.last_vision_radius = None
        self.dungeon_clear_count = 0
        self.dungeon_clear_goal = 5
        self.dragged_weapon_idx = None
        self.dragged_chain_idx = None
        self.inventory_rects = []
        self.selected_chain_idx = 0
        self.selected_weapon_slot_idx = None
        self.inventory_mode = "chains"
        self.menu_rects = []
        self.selected_npc_menu_option = None
        self.selected_menu_option = None  # Reset to detect hover

    def _initialize_fog_map(self):
        """Create a fog map to track visible dungeon areas."""
        self.fog_map = [[False for _ in range(self.dungeon.grid_width)]
                       for _ in range(self.dungeon.grid_height)]

    def _get_room_center(self, room):
        """Calculate the center position of a room in pixels."""
        center_x = int(room.x + room.width // 2) * TILE_SIZE
        center_y = int(room.y + room.height // 2) * TILE_SIZE
        return center_x, center_y

    def initialize_lobby(self):
        """Set up the lobby room with player and NPC at their spawn points."""
        self.dungeon.initialize_lobby()
        self.current_room_id = 0
        spawn_room = self.dungeon.get_room(self.current_room_id)

        player_pos = None
        npc_pos = None
        for row in range(int(spawn_room.height)):
            for col in range(int(spawn_room.width)):
                if spawn_room.tiles[row][col] == 'Player_spawn':
                    player_pos = ((spawn_room.x + col) * TILE_SIZE + TILE_SIZE // 2, (spawn_room.y + row) * TILE_SIZE + TILE_SIZE // 2)
                elif spawn_room.tiles[row][col] == 'NPC_spawn':
                    npc_pos = ((spawn_room.x + col) * TILE_SIZE + TILE_SIZE // 2, (spawn_room.y + row) * TILE_SIZE + TILE_SIZE // 2)

        if player_pos is None:
            raise ValueError("Player spawn point not found in the lobby room.")
        if npc_pos is None:
            raise ValueError("NPC spawn point not found in the lobby room.")

        self.player = Player(pos=player_pos, game=self)
        self.player.skills = [(skill, 'right_click') for skill, _ in self.selected_skills]
        self.player.weapons = self.selected_weapons
        # Initialize weapon_chain with max_weapon_chains empty lists
        self.player.weapon_chain = [[] for _ in range(self.player.max_weapon_chains)]
        self.player.weapon_chain[0] = self.selected_weapons[:self.player.max_weapon_chain_length]
        self.npc_group.add(NPC(pos=npc_pos, game=self))

        self._update_camera_initial()
        self._initialize_minimap()
        self._initialize_fog_map()
        self._update_fog_map_from_player()

    def _initialize_minimap(self):
        """Set up minimap dimensions and offset."""
        self.minimap_width = int(self.dungeon.grid_width * self.minimap_scale)
        self.minimap_height = int(self.dungeon.grid_height * self.minimap_scale)
        self.minimap_offset = (SCREEN_WIDTH - self.minimap_width - 10, 10)

    def _update_camera_initial(self):
        """Initialize camera offset based on player position."""
        self.camera_offset = [
            -(self.player.pos[0] - SCREEN_WIDTH // 2),
            -(self.player.pos[1] - SCREEN_HEIGHT // 2)
        ]

    def _update_fog_map_from_player(self):
        """Update fog map based on player's current position."""
        tile_x = int(self.player.pos[0] / TILE_SIZE)
        tile_y = int(self.player.pos[1] / TILE_SIZE)
        self.update_fog_map(tile_x, tile_y)

    def start_game(self):
        """Start a new game by initializing dungeon and enemies."""
        self.dungeon_clear_count = 0
        self._start_new_dungeon()
        self._generate_entities()

    def _start_new_dungeon(self):
        """Initialize a new dungeon and reset player position."""
        self.dungeon.initialize_dungeon()
        self.current_room_id = self._find_start_room()
        spawn_room = self.dungeon.get_room(self.current_room_id)
        center_x, center_y = self._get_room_center(spawn_room)

        if not self.player:
            self.player = Player(pos=(center_x, center_y), game=self)
        else:
            self.player.pos = (center_x, center_y)
            self.player.rect.x = center_x
            self.player.rect.y = center_y
            self.player.health = self.player.max_health
            self.player.energy = self.player.max_energy

        self.player.skills = [(skill, 'right_click') for skill, _ in self.selected_skills]
        for skill, _ in self.player.skills:
            if skill.cooldown == 0:
                skill.use(self.player, self, self.current_time)
        self.player.weapons = self.selected_weapons
        # Initialize weapon_chain with max_weapon_chains empty lists
        self.player.weapon_chain = [[] for _ in range(self.player.max_weapon_chains)]
        self.player.weapon_chain[0] = self.selected_weapons[:self.player.max_weapon_chain_length]
        self.state = "playing"

        self._update_camera_initial()
        self._initialize_minimap()
        self._initialize_fog_map()
        self._update_fog_map_from_player()
        self.last_player_pos = None
        self.last_vision_radius = None

    def _find_start_room(self):
        """Find the ID of the dungeon's start room."""
        for room in self.dungeon.rooms:
            if room.room_type == RoomType.START:
                return room.id
        return 0

    def _generate_entities(self):
        """Clear existing enemies and spawn new ones randomly."""
        self.enemy_group.empty()
        self.enemy_bullet_group.empty()
        self.player_bullet_group.empty()
        self.damage_text_group.empty()
        self.npc_group.empty()
        self.trap_group.empty()
        self.reward_group.empty()
        self.environment_group.empty()

        for room in self.dungeon.rooms:
            if room.room_type == RoomType.MONSTER:
                for row in range(int(room.height)):
                    for col in range(int(room.width)):
                        if room.tiles[row][col] == 'Monster_spawn':
                            enemy_pos = (
                                (room.x + col) * TILE_SIZE + TILE_SIZE // 2,
                                (room.y + row) * TILE_SIZE + TILE_SIZE // 2
                            )
                            self.enemy_group.add(BasicEnemy(pos=enemy_pos, game=self))

    def update_fog_map(self, tile_x: int, tile_y: int):
        """Update fog of war based on player's vision radius."""
        vision_radius = self.player.vision_radius
        for y in range(max(0, tile_y - vision_radius),
                      min(self.dungeon.grid_height, tile_y + vision_radius + 1)):
            for x in range(max(0, tile_x - vision_radius),
                          min(self.dungeon.grid_width, tile_x + vision_radius + 1)):
                if math.sqrt((x - tile_x) ** 2 + (y - tile_y) ** 2) <= vision_radius:
                    try:
                        self.fog_map[y][x] = True
                    except IndexError:
                        pass

    def update_fog_surface(self):
        """Update the fog surface to reflect visible areas."""
        self.fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.fog_surface.fill((0, 0, 0, 255))

        if not self.player.fog:
            self.fog_surface.fill((0, 0, 0, 0))
            return

        center_x = self.player.rect.centerx + self.camera_offset[0]
        center_y = self.player.rect.centery + self.camera_offset[1]
        radius = int(self.player.vision_radius * TILE_SIZE)

        points = []
        for angle in range(0, 360, 1):
            rad = math.radians(angle)
            dx, dy = math.cos(rad), math.sin(rad)
            current_x, current_y = self.player.pos
            max_steps = int(radius / 2)

            for _ in range(max_steps):
                current_x += dx * 2
                current_y += dy * 2
                tile_x = int(current_x / TILE_SIZE)
                tile_y = int(current_y / TILE_SIZE)

                if (tile_x < 0 or tile_x >= self.dungeon.grid_width or
                    tile_y < 0 or tile_y >= self.dungeon.grid_height or
                    self.dungeon.dungeon_tiles[tile_y][tile_x] == 'Border_wall'):
                    break

            screen_x = current_x + self.camera_offset[0]
            screen_y = current_y + self.camera_offset[1]
            points.append((screen_x, screen_y))

        if points:
            pygame.draw.polygon(self.fog_surface, (0, 0, 0, 0), points)

    def _get_tile_color(self, tile: str, is_wall: bool = False):
        """Return the appropriate color for a given tile type."""
        if tile == 'Border_wall' and is_wall:
            return BORDER_WALL_SIDE_COLOR
        elif tile == 'Border_wall':
            return BORDER_WALL_TOP_COLOR

        if tile not in ROOM_FLOOR_COLORS:
            return ROOM_FLOOR_COLORS['Outside']
        return ROOM_FLOOR_COLORS[tile]

    def draw_3d_walls(self, row, col, x, y, tile, is_wall=False):
        """Draw a tile with 3D wall effect if applicable."""
        if is_wall and tile == 'Border_wall':
            wall_shift = int(TILE_SIZE * 0.65)
            wall_height = TILE_SIZE
            pygame.draw.rect(self.screen, BORDER_WALL_SIDE_COLOR, (x, y, TILE_SIZE, wall_height))
            pygame.draw.rect(self.screen, BORDER_WALL_TOP_COLOR, (x, y - wall_shift, TILE_SIZE, TILE_SIZE))
        else:
            color = self._get_tile_color(tile, is_wall)
            pygame.draw.rect(self.screen, color, (x, y, TILE_SIZE, TILE_SIZE))

    def draw_minimap(self):
        """Draw the minimap showing explored areas and player position."""
        minimap_surface = pygame.Surface((self.minimap_width, self.minimap_height))
        minimap_surface.fill((0, 0, 0))

        for room in self.dungeon.rooms:
            for row in range(int(room.height)):
                for col in range(int(room.width)):
                    grid_x = int(room.x + col)
                    grid_y = int(room.y + row)
                    if (0 <= grid_y < self.dungeon.grid_height and
                        0 <= grid_x < self.dungeon.grid_width and
                        self.fog_map[grid_y][grid_x]):
                        minimap_x = int(grid_x * self.minimap_scale)
                        minimap_y = int(grid_y * self.minimap_scale)
                        tile = room.tiles[row][col]
                        color = self._get_tile_color(tile)
                        pygame.draw.rect(minimap_surface, color, (minimap_x, minimap_y, 1, 1))

        for y in range(self.dungeon.grid_height):
            for x in range(self.dungeon.grid_width):
                if self.fog_map[y][x] and self.dungeon.dungeon_tiles[y][x] == 'Bridge_floor':
                    minimap_x = int(x * self.minimap_scale)
                    minimap_y = int(y * self.minimap_scale)
                    color = ROOM_FLOOR_COLORS['Bridge_floor']
                    pygame.draw.rect(minimap_surface, color, (minimap_x, minimap_y, 1, 1))

        if self.player:
            player_minimap_x = int(self.player.pos[0] / TILE_SIZE * self.minimap_scale)
            player_minimap_y = int(self.player.pos[1] / TILE_SIZE * self.minimap_scale)
            pygame.draw.circle(minimap_surface, (0, 255, 0), (player_minimap_x, player_minimap_y), 3)

        self.screen.blit(minimap_surface, self.minimap_offset)

    def update_camera(self, dt: float):
        """Smoothly update camera position to follow the player."""
        target_offset_x = -(self.player.pos[0] - SCREEN_WIDTH // 2)
        target_offset_y = -(self.player.pos[1] - SCREEN_HEIGHT // 2)
        self.camera_offset[0] += (target_offset_x - self.camera_offset[0]) * self.camera_lerp_factor * dt
        self.camera_offset[1] += (target_offset_y - self.camera_offset[1]) * self.camera_lerp_factor * dt

    def _handle_player_movement(self, dt: float):
        """Handle player movement based on keyboard input."""
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if dx != 0 or dy != 0:
            length = math.sqrt(dx**2 + dy**2)
            dx /= length
            dy /= length
        self.player.move(dx, dy, dt)

    def _handle_player_firing(self, dt: float):
        """Handle player firing based on mouse input."""
        mouse_pos = pygame.mouse.get_pos()
        direction = (
            mouse_pos[0] - (self.player.pos[0] + self.camera_offset[0]),
            mouse_pos[1] - (self.player.pos[1] + self.camera_offset[1])
        )
        target_position = (
            self.player.pos[0] + direction[0],
            self.player.pos[1] + direction[1]
        )
        length = math.sqrt(direction[0]**2 + direction[1]**2)
        if length > 0:
            direction = (direction[0] / length, direction[1] / length)
        if pygame.mouse.get_pressed()[0]:
            bullet = self.player.fire(direction, self.current_time, target_position)
            if bullet:
                self.player_bullet_group.add(bullet)

    def _handle_skill_activation(self, events):
        """Activate a skill based on right-click."""
        mouse_pos = pygame.mouse.get_pos()
        direction = (
            mouse_pos[0] - (self.player.pos[0] + self.camera_offset[0]),
            mouse_pos[1] - (self.player.pos[1] + self.camera_offset[1])
        )
        length = math.sqrt(direction[0]**2 + direction[1]**2)
        if length > 0:
            direction = (direction[0] / length, direction[1] / length)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                print("Right click detected, activating skill")
                skill = self.player.skills[self.player.current_skill_idx][0] if self.player.skills else None
                if skill and skill.can_use(self.player, self.current_time):
                    skill.use(self.player, self, self.current_time, direction)
                    print(f"Skill {skill.name} used")

    def _handle_weapon_selection(self, events):
        """Handle weapon chain selection with 1-9 keys."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                               pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                    idx = event.key - pygame.K_1
                    if idx < self.player.max_weapon_chains and self.player.weapon_chain[idx]:
                        self.player.current_weapon_chain_idx = idx
                        self.player.current_weapon_idx = 0
                        print(f"Selected weapon chain {idx + 1}: {self.player.weapon_chain[idx][0].name if self.player.weapon_chain[idx] else 'Empty'}")

    def _update_bullets(self, dt: float):
        """Update bullets and handle collisions."""
        for bullet in self.player_bullet_group.copy():
            if not bullet.update(dt):
                self.player_bullet_group.remove(bullet)
            else:
                for enemy in self.enemy_group:
                    hitted, damage = bullet.check_collision(enemy, self.current_time)
                    if damage > 0:
                        damage_text = DamageText(enemy.pos, damage)
                        self.damage_text_group.add(damage_text)
                    if hitted:
                        self.player_bullet_group.remove(bullet)
                        break

        for bullet in self.enemy_bullet_group.copy():
            if not bullet.update(dt):
                self.enemy_bullet_group.remove(bullet)
            elif bullet.shooter != self.player :
                hitted, damage = bullet.check_collision(self.player, self.current_time)
                if damage > 0:
                    damage_text = DamageText(self.player.pos, damage)
                    self.damage_text_group.add(damage_text)
                if hitted:
                    self.enemy_bullet_group.remove(bullet)
                if self.player.health <= 0:
                    print("Player died!")

    def _update_enemies(self, dt: float):
        """Update enemies and remove dead ones."""
        for enemy in self.enemy_group.copy():
            if enemy.health <= 0:
                self.enemy_group.remove(enemy)
            else:
                enemy.update(dt, self.current_time)
                damage = enemy.check_collision_with_player(self.current_time)
                if damage > 0:
                    damage_text = DamageText(self.player.pos, damage)
                    self.damage_text_group.add(damage_text)
                    
    def _update_damage_text(self, dt: float):
        """Update damage text display."""
        for damage_text in self.damage_text_group.copy():
            if not damage_text.update(dt):
                self.damage_text_group.remove(damage_text)
                
    def _check_dungeon_completion(self):
        """Check if player reached the end portal and handle dungeon progression."""
        if self.dungeon.get_tile_at(self.player.pos) == 'End_room_portal':
            self.dungeon_clear_count += 1
            if self.dungeon_clear_count >= self.dungeon_clear_goal:
                self.state = "win"
            else:
                print(f"已通過 {self.dungeon_clear_count} 次地牢，進入下一層！")
                self._start_new_dungeon()
                self._generate_entities()

    def update(self, dt: float):
        """Update game state based on current mode."""
        self.current_time += dt * self.time_scale
        dt *= self.time_scale
        if self.player and self.player.invulnerable > 0:
            self.player.invulnerable -= dt

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return False

        if self.state == "menu":
            return self._update_menu(events)
        elif self.state == "lobby":
            return self._update_lobby(dt, events)
        elif self.state == "npc_menu":
            return self._update_npc_menu(events)
        elif self.state == "select_skill":
            return self._update_skill_selection(events)
        elif self.state == "select_weapons":
            return self._update_weapon_selection(events)
        elif self.state == "playing":
            return self._update_playing(dt, events)
        elif self.state == "inventory":
            return self._update_inventory(events)
        return True

    def _update_menu(self, events):
        """Handle menu navigation and selection with keyboard and mouse."""
        mouse_pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self.menu_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_menu_option = i
                break
        if self.selected_menu_option is None:
            self.selected_menu_option = 0  # Default to first option if no hover

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_menu_option = (self.selected_menu_option - 1) % len(self.menu_options)
                    print(f"Selected menu option: {self.menu_options[self.selected_menu_option]}")
                elif event.key == pygame.K_DOWN:
                    self.selected_menu_option = (self.selected_menu_option + 1) % len(self.menu_options)
                    print(f"Selected menu option: {self.menu_options[self.selected_menu_option]}")
                elif event.key == pygame.K_RETURN:
                    if self.menu_options[self.selected_menu_option] == "Enter Lobby":
                        if self.skills_library:
                            self.state = "lobby"
                            self.initialize_lobby()
                            print("Entering lobby")
                        else:
                            print("No skills available, cannot start game")
                    else:
                        print("Exiting game")
                        return False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(self.menu_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_menu_option = i
                        if self.menu_options[i] == "Enter Lobby":
                            if self.skills_library:
                                self.state = "lobby"
                                self.initialize_lobby()
                                print("Entering lobby via mouse click")
                            else:
                                print("No skills available, cannot start game")
                        else:
                            print("Exiting game via mouse click")
                            return False
                        break
        return True

    def _update_lobby(self, dt: float, events):
        """Update lobby state with player movement and NPC interaction."""
        self._handle_player_movement(dt)
        self.player.update(dt, self.current_time)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    for npc in self.npc_group:
                        if npc.can_interact(self.player.pos):
                            self.state = "npc_menu"
                            self.selected_npc_menu_option = 0
                            break
                    else:
                        self.state = "inventory"
                        self.inventory_rects = []
                        self.selected_chain_idx = self.player.current_weapon_chain_idx
                        self.selected_weapon_slot_idx = None
                        self.inventory_mode = "chains"
                elif event.key == pygame.K_c:
                    self.player.current_skill_idx = (self.player.current_skill_idx + 1) % len(self.player.skills) if self.player.skills else 0
                    print(f"Changed to skill: {self.player.skills[self.player.current_skill_idx][0].name if self.player.skills else 'None'}")
                else:
                    self._handle_weapon_selection([event])
            self._handle_skill_activation([event])

        self._handle_player_firing(dt)
        self._update_bullets(dt)
        self._update_enemies(dt)
        self._update_damage_text(dt)
        self.update_camera(dt)
        self._update_fog_map_from_player()
        self.update_fog_surface()
        self.player.update(dt, self.current_time)
        self.last_player_pos = (self.player.pos[0], self.player.pos[1])
        self.last_vision_radius = self.player.vision_radius
        return True

    def _update_npc_menu(self, events):
        """Handle NPC menu navigation and selection with keyboard and mouse."""
        mouse_pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self.npc_menu_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_npc_menu_option = i
                break
        if self.selected_npc_menu_option is None:
            self.selected_npc_menu_option = 0  # Default to first option if no hover

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_npc_menu_option = (self.selected_npc_menu_option - 1) % len(self.npc_menu_options)
                    print(f"Selected NPC menu option: {self.npc_menu_options[self.selected_npc_menu_option]}")
                elif event.key == pygame.K_DOWN:
                    self.selected_npc_menu_option = (self.selected_npc_menu_option + 1) % len(self.npc_menu_options)
                    print(f"Selected NPC menu option: {self.npc_menu_options[self.selected_npc_menu_option]}")
                elif event.key == pygame.K_RETURN:
                    if self.npc_menu_options[self.selected_npc_menu_option] == "Select Skills":
                        if self.skills_library:
                            self.state = "select_skill"
                            self.selected_skill = self.skills_library[0]
                            print("Entered skill selection")
                        else:
                            print("No skills available")
                    elif self.npc_menu_options[self.selected_npc_menu_option] == "Select Weapons":
                        self.state = "select_weapons"
                        print("Entered weapon selection")
                    elif self.npc_menu_options[self.selected_npc_menu_option] == "Start Game":
                        if self.selected_weapons and self.selected_skills:
                            self.start_game()
                            print("Started game")
                        else:
                            print("Must select at least one skill and one weapon")
                elif event.key == pygame.K_ESCAPE:
                    self.state = "lobby"
                    self.player.skills = [(skill, 'right_click') for skill, _ in self.selected_skills]
                    print("Returned to lobby from NPC menu")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(self.npc_menu_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_npc_menu_option = i
                        if self.npc_menu_options[i] == "Select Skills":
                            if self.skills_library:
                                self.state = "select_skill"
                                self.selected_skill = self.skills_library[0]
                                print("Entered skill selection via mouse click")
                            else:
                                print("No skills available")
                        elif self.npc_menu_options[i] == "Select Weapons":
                            self.state = "select_weapons"
                            print("Entered weapon selection via mouse click")
                        elif self.npc_menu_options[i] == "Start Game":
                            if self.selected_weapons and self.selected_skills:
                                self.start_game()
                                print("Started game via mouse click")
                            else:
                                print("Must select at least one skill and one weapon")
                        break
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:  # Scroll up
                    self.selected_npc_menu_option = (self.selected_npc_menu_option - 1) % len(self.npc_menu_options)
                    self.selected_skill = self.skills_library[self.selected_npc_menu_option]
                    print(f"Scrolled to NPC menu option: {self.npc_menu_options[self.selected_npc_menu_option]}")
                elif event.y < 0:  # Scroll down
                    self.selected_npc_menu_option = (self.selected_npc_menu_option + 1) % len(self.npc_menu_options)
                    self.selected_skill = self.skills_library[self.selected_npc_menu_option]
                    print(f"Scrolled to NPC menu option: {self.npc_menu_options[self.selected_npc_menu_option]}")
        return True

    def _update_skill_selection(self, events):
        """Handle skill selection and key binding with keyboard and mouse."""
        if not self.skills_library or not self.player:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "npc_menu"
                    self.selected_skill = None
                    print("Returned to NPC menu from skill selection")
            return True

        mouse_pos = pygame.mouse.get_pos()
        current_idx = self.skills_library.index(self.selected_skill) if self.selected_skill in self.skills_library else 0
        for i, rect in enumerate(self.skill_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_skill = self.skills_library[i]
                current_idx = i
                break

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    current_idx = (current_idx - 1) % len(self.skills_library)
                    self.selected_skill = self.skills_library[current_idx]
                    print(f"Selected skill: {self.selected_skill.name}")
                elif event.key == pygame.K_DOWN:
                    current_idx = (current_idx + 1) % len(self.skills_library)
                    self.selected_skill = self.skills_library[current_idx]
                    print(f"Selected skill: {self.selected_skill.name}")
                elif event.key == pygame.K_RETURN:
                    if len(self.selected_skills) < self.player.max_skills:
                        if self.selected_skill not in [skill for skill, _ in self.selected_skills]:
                            self.selected_skills.append((self.selected_skill, 'right_click'))
                            print(f"Skill {self.selected_skill.name} selected")
                        else:
                            self.selected_skills = [(skill, key) for skill, key in self.selected_skills if skill != self.selected_skill]
                            print(f"Skill {self.selected_skill.name} removed via ENTER")
                    else:
                        print(f"Maximum {self.player.max_skills} skills can be selected")
                elif event.key == pygame.K_ESCAPE:
                    self.state = "npc_menu"
                    self.player.skills = [(skill, 'right_click') for skill, _ in self.selected_skills]
                    print("Returned to NPC menu from skill selection")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(self.skill_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_skill = self.skills_library[i]
                        if event.button == 1:  # Left-click
                            if len(self.selected_skills) < self.player.max_skills:
                                if self.selected_skill not in [skill for skill, _ in self.selected_skills]:
                                    self.selected_skills.append((self.selected_skill, 'right_click'))
                                    print(f"Skill {self.selected_skill.name} selected via left-click")
                                else:
                                    self.selected_skills = [(skill, key) for skill, key in self.selected_skills if skill != self.selected_skill]
                                    print(f"Skill {self.selected_skill.name} removed via left-click")
                            else:
                                print(f"Maximum {self.player.max_skills} skills can be selected")
                        elif event.button == 3:  # Right-click
                            if self.selected_skill in [skill for skill, _ in self.selected_skills]:
                                self.selected_skills = [(skill, key) for skill, key in self.selected_skills if skill != self.selected_skill]
                                print(f"Skill {self.selected_skill.name} removed via right-click")
                        break
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:  # Scroll up
                    current_idx = (current_idx - 1) % len(self.skills_library)
                    self.selected_skill = self.skills_library[current_idx]
                    print(f"Scrolled to skill: {self.selected_skill.name}")
                elif event.y < 0:  # Scroll down
                    current_idx = (current_idx + 1) % len(self.skills_library)
                    self.selected_skill = self.skills_library[current_idx]
                    print(f"Scrolled to skill: {self.selected_skill.name}")
        return True

    def _update_weapon_selection(self, events):
        """Handle weapon selection and removal with keyboard and mouse."""
        max_weapons = self.player.max_weapons if self.player else MAX_WEAPONS_DEFAULT
        selected_weapon_idx = self.weapons_library.index(self.selected_weapons[0]) if self.selected_weapons else 0

        mouse_pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self.weapon_rects):
            if rect.collidepoint(mouse_pos):
                selected_weapon_idx = i
                break

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_weapon_idx = (selected_weapon_idx - 1) % len(self.weapons_library)
                    print(f"Selected weapon: {self.weapons_library[selected_weapon_idx].name}")
                elif event.key == pygame.K_DOWN:
                    selected_weapon_idx = (selected_weapon_idx + 1) % len(self.weapons_library)
                    print(f"Selected weapon: {self.weapons_library[selected_weapon_idx].name}")
                elif event.key == pygame.K_RETURN:
                    if len(self.selected_weapons) < max_weapons:
                        selected_weapon = self.weapons_library[selected_weapon_idx]
                        self.selected_weapons.append(selected_weapon)
                        self.player.weapon_chain[0].append(selected_weapon)
                        if len(self.player.weapon_chain[0]) > self.player.max_weapon_chain_length:
                            self.player.weapon_chain[0].pop(0)
                        print(f"Selected weapon: {selected_weapon.name}")
                    else:
                        print(f"Maximum {max_weapons} weapons can be selected")
                elif event.key == pygame.K_BACKSPACE and self.selected_weapons:
                    removed_weapon = self.selected_weapons.pop()
                    for chain in self.player.weapon_chain:
                        if removed_weapon in chain:
                            chain.remove(removed_weapon)
                    print(f"Removed weapon: {removed_weapon.name} via BACKSPACE")
                elif event.key == pygame.K_ESCAPE:
                    self.state = "npc_menu"
                    print("Returned to NPC menu from weapon selection")
                elif event.key == pygame.K_SPACE:
                    if self.selected_weapons:
                        self.player.weapons = self.selected_weapons
                        self.player.weapon_chain[0] = self.selected_weapons[:self.player.max_weapon_chain_length]
                        self.state = "npc_menu"
                        print("Confirmed weapon selection and returned to NPC menu")
                    else:
                        print("At least one weapon must be selected")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(self.weapon_rects):
                    if rect.collidepoint(event.pos):
                        selected_weapon = self.weapons_library[i]
                        if event.button == 1:  # Left-click
                            if selected_weapon in self.selected_weapons:
                                self.selected_weapons.remove(selected_weapon)
                                for chain in self.player.weapon_chain:
                                    if selected_weapon in chain:
                                        chain.remove(selected_weapon)
                                print(f"Removed weapon: {selected_weapon.name} via left-click")
                            elif len(self.selected_weapons) < max_weapons:
                                self.selected_weapons.append(selected_weapon)
                                self.player.weapon_chain[0].append(selected_weapon)
                                if len(self.player.weapon_chain[0]) > self.player.max_weapon_chain_length:
                                    self.player.weapon_chain[0].pop(0)
                                print(f"Selected weapon: {selected_weapon.name} via left-click")
                            else:
                                print(f"Maximum {max_weapons} weapons can be selected")
                        elif event.button == 3:  # Right-click
                            if selected_weapon in self.selected_weapons:
                                self.selected_weapons.remove(selected_weapon)
                                for chain in self.player.weapon_chain:
                                    if selected_weapon in chain:
                                        chain.remove(selected_weapon)
                                print(f"Removed weapon: {selected_weapon.name} via right-click")
                        break
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:  # Scroll up
                    selected_weapon_idx = (selected_weapon_idx - 1) % len(self.weapons_library)
                    print(f"Scrolled to weapon: {self.weapons_library[selected_weapon_idx].name}")
                elif event.y < 0:  # Scroll down
                    selected_weapon_idx = (selected_weapon_idx + 1) % len(self.weapons_library)
                    print(f"Scrolled to weapon: {self.weapons_library[selected_weapon_idx].name}")
        return True


    def _update_inventory(self, events):
        """Handle inventory state for weapon chain customization with 3x3 grid and player weapons."""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.inventory_mode == "chains":
                    for chain_idx, rect in enumerate(self.inventory_rects):
                        if rect.collidepoint(event.pos):
                            self.selected_chain_idx = chain_idx
                            self.selected_weapon_slot_idx = None
                            self.inventory_mode = "chain_details"
                            print(f"Selected chain {chain_idx + 1}")
                            break
                    done_rect = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50, 100, 40)
                    if done_rect.collidepoint(event.pos):
                        self._save_weapon_chains()
                        self.state = "lobby"
                        self.inventory_mode = "chains"
                        self.selected_chain_idx = self.player.current_weapon_chain_idx
                        self.selected_weapon_slot_idx = None
                        print("Saved weapon chains and returned to lobby")
                elif self.inventory_mode == "chain_details":
                    chain = self.player.weapon_chain[self.selected_chain_idx] if self.selected_chain_idx < len(self.player.weapon_chain) else []
                    for slot_idx, (slot_rect, plus_rect, minus_rect) in enumerate(self.inventory_rects[self.selected_chain_idx]):
                        if slot_rect.collidepoint(event.pos):
                            self.selected_weapon_slot_idx = slot_idx
                            self.inventory_mode = "weapon_selection"
                            print(f"Selected slot {slot_idx + 1} in chain {self.selected_chain_idx + 1}")
                            break
                        elif plus_rect.collidepoint(event.pos):
                            if len(chain) < self.player.max_weapon_chain_length:
                                # Ensure chain exists
                                if self.selected_chain_idx >= len(self.player.weapon_chain):
                                    self.player.weapon_chain.extend([[] for _ in range(self.selected_chain_idx - len(self.player.weapon_chain) + 1)])
                                self.player.weapon_chain[self.selected_chain_idx].insert(slot_idx + 1, None)
                                print(f"Added empty slot after position {slot_idx} in chain {self.selected_chain_idx + 1}")
                            else:
                                print(f"Cannot add slot: Chain {self.selected_chain_idx + 1} at max length ({self.player.max_weapon_chain_length})")
                            break
                        elif minus_rect.collidepoint(event.pos):
                            if len(chain) > 1:
                                removed_weapon = self.player.weapon_chain[self.selected_chain_idx].pop(slot_idx)
                                if removed_weapon:
                                    print(f"Removed weapon {removed_weapon.name} from slot {slot_idx + 1} in chain {self.selected_chain_idx + 1}")
                                else:
                                    print(f"Removed empty slot {slot_idx + 1} from chain {self.selected_chain_idx + 1}")
                            elif len(chain) == 1:
                                self.player.weapon_chain[self.selected_chain_idx].pop(slot_idx)
                                if self.player.current_weapon_chain_idx == self.selected_chain_idx:
                                    self.player.current_weapon_idx = 0
                                print(f"Cleared last slot in chain {self.selected_chain_idx + 1}")
                            else:
                                print(f"Cannot remove slot: Chain {self.selected_chain_idx + 1} is empty")
                            break
                elif self.inventory_mode == "weapon_selection":
                    chain = self.player.weapon_chain[self.selected_chain_idx] if self.selected_chain_idx < len(self.player.weapon_chain) else []
                    used_weapons = set(weapon for weapon in chain if weapon is not None)
                    available_weapons = [weapon for weapon in self.player.weapons if weapon not in used_weapons]
                    for weapon_idx, rect in enumerate(self.inventory_rects):
                        if rect.collidepoint(event.pos):
                            if weapon_idx < len(available_weapons):
                                selected_weapon = available_weapons[weapon_idx]
                                if self.selected_chain_idx >= len(self.player.weapon_chain):
                                    self.player.weapon_chain.extend([[] for _ in range(self.selected_chain_idx - len(self.player.weapon_chain) + 1)])
                                self.player.weapon_chain[self.selected_chain_idx][self.selected_weapon_slot_idx] = selected_weapon
                                print(f"Assigned {selected_weapon.name} to slot {self.selected_weapon_slot_idx + 1} in chain {self.selected_chain_idx + 1}")
                                self.inventory_mode = "chain_details"
                                self.selected_weapon_slot_idx = None
                            else:
                                print(f"Invalid weapon index {weapon_idx} clicked")
                            break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.inventory_mode == "chains":
                        self.state = "lobby"
                        self.selected_chain_idx = self.player.current_weapon_chain_idx
                        self.selected_weapon_slot_idx = None
                        print("Returned to lobby from chains mode")
                    elif self.inventory_mode == "chain_details":
                        self.inventory_mode = "chains"
                        self.selected_weapon_slot_idx = None
                        print("Returned to chains mode from chain_details")
                    elif self.inventory_mode == "weapon_selection":
                        self.inventory_mode = "chain_details"
                        self.selected_weapon_slot_idx = None
                        print("Returned to chain_details from weapon_selection")
                else:
                    self._handle_weapon_selection([event])
        return True

    def _update_playing(self, dt: float, events):
        """Update gameplay state with player actions and game logic."""
        self._handle_player_movement(dt)
        self.player.update(dt, self.current_time)
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    if self.player.skills:
                        self.player.current_skill_idx = (self.player.current_skill_idx + 1) % len(self.player.skills)
                        print(f"Changed to skill: {self.player.skills[self.player.current_skill_idx][0].name}")
                elif event.key == pygame.K_r:
                    if self.dungeon_clear_count >= self.dungeon_clear_goal:
                        self.state = "win"
                    else:
                        print(f"已通過 {self.dungeon_clear_count} 次地牢，進入下一層！")
                        self._start_new_dungeon()
                        self._generate_entities()
                elif event.key == pygame.K_e:
                    for npc in self.npc_group:
                        if npc.can_interact(self.player.pos):
                            self.state = "npc_menu"
                            self.selected_npc_menu_option = 0
                            break
                    else:
                        self.state = "inventory"
                        self.inventory_rects = []
                        self.selected_chain_idx = self.player.current_weapon_chain_idx
                        self.selected_weapon_slot_idx = None
                        self.inventory_mode = "chains"
                        
        self._handle_skill_activation(events)
        self._handle_player_firing(dt)
        self.player.update(dt, self.current_time)
        self._update_bullets(dt)
        self._update_enemies(dt)
        self._update_damage_text(dt)
        self.update_camera(dt)
        self._update_fog_map_from_player()
        self.update_fog_surface()
        self.last_player_pos = (self.player.pos[0], self.player.pos[1])
        self.last_vision_radius = self.player.vision_radius
        self._check_dungeon_completion()
        return True
    
    def _save_weapon_chains(self):
        """Save weapon chains, remove empty slots, and update selected weapons."""
        for chain in self.player.weapon_chain:
            chain[:] = [weapon for weapon in chain if weapon is not None]
        self.player.weapons = []
        for chain in self.player.weapon_chain:
            self.player.weapons.extend(chain)
        self.player.weapons = list(dict.fromkeys(self.player.weapons))
        self.selected_weapons = self.player.weapons[:]
        print("Weapon chains saved, empty slots removed")

    def _draw_hud(self):
        """Draw heads-up display with player stats and progress."""
        font = pygame.font.SysFont(None, 36)
        self.screen.blit(font.render(f"Health: {self.player.health}/{self.player.max_health}", True, (255, 255, 255)), (10, 10))
        self.screen.blit(font.render(f"Energy: {int(self.player.energy)}/{int(self.player.max_energy)}", True, (255, 255, 255)), (10, 50))

        if self.player.weapon_chain[self.player.current_weapon_chain_idx]:
            weapon = self.player.weapon_chain[self.player.current_weapon_chain_idx][self.player.current_weapon_idx]
            self.screen.blit(font.render(f"Chain {self.player.current_weapon_chain_idx + 1}: {weapon.name} (Energy: {weapon.energy_cost}/Shot)", True, (255, 255, 255)), (10, 90))

        y_offset = 130
        skill = self.player.skills[self.player.current_skill_idx][0] if self.player.skills else None
        if skill:
            self.screen.blit(font.render(f"Skill: {skill.name}", True, (255, 255, 255)), (10, y_offset))
            if skill.cooldown > 0:
                cooldown = max(0, skill.cooldown - (self.current_time - skill.last_used))
                self.screen.blit(font.render(f"CD: {cooldown:.1f}s", True, (255, 255, 255)), (150, y_offset))

        if self.state == "playing":
            progress_text = font.render(f"Dungeon: {self.dungeon_clear_count+1}/{self.dungeon_clear_goal}", True, (255, 255, 0))
            self.screen.blit(progress_text, (10, y_offset + 40))

    def draw_inventory(self):
        """Draw the inventory interface with 3x3 chain grid on left and player weapons on right."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
        title = font.render("Inventory: Select chain, edit weapons, press ESC to exit", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 36))

        self.inventory_rects = []

        if self.inventory_mode == "chains":
            self.inventory_rects = []
            grid_size = 100
            grid_spacing = 20
            start_x = 50
            start_y = 100
            for chain_idx in range(self.player.max_weapon_chains):
                row = chain_idx // 3
                col = chain_idx % 3
                x = start_x + col * (grid_size + grid_spacing)
                y = start_y + row * (grid_size + grid_spacing)
                rect = pygame.Rect(x, y, grid_size, grid_size)
                color = (255, 255, 0) if chain_idx == self.selected_chain_idx else (255, 255, 255)
                pygame.draw.rect(self.screen, color, rect, 2)
                # Safely access chain; use empty list if not initialized
                chain = self.player.weapon_chain[chain_idx] if chain_idx < len(self.player.weapon_chain) else []
                text = font.render(f"Chain {chain_idx + 1}: {len(chain)}", True, color)
                self.screen.blit(text, (x + 10, y + 10))
                self.inventory_rects.append(rect)

            done_text = font.render("Done", True, (255, 255, 255))
            done_rect = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 50, 100, 40)
            pygame.draw.rect(self.screen, (0, 255, 0), done_rect, 2)
            self.screen.blit(done_text, (done_rect.x + 10, done_rect.y + 10))

        elif self.inventory_mode == "chain_details":
            chain = self.player.weapon_chain[self.selected_chain_idx] if self.selected_chain_idx < len(self.player.weapon_chain) else []
            self.inventory_rects = [[] for _ in range(self.player.max_weapon_chains)]
            x_offset = 50
            y_offset = 100
            chain_title = font.render(f"Chain {self.selected_chain_idx + 1}", True, (255, 255, 255))
            self.screen.blit(chain_title, (x_offset, y_offset))
            y_offset += 40

            chain_rects = []
            if not chain:
                # Add initial slot for empty chain
                if self.selected_chain_idx < len(self.player.weapon_chain):
                    self.player.weapon_chain[self.selected_chain_idx] = [None]
                else:
                    self.player.weapon_chain.extend([[] for _ in range(self.selected_chain_idx - len(self.player.weapon_chain) + 1)])
                    self.player.weapon_chain[self.selected_chain_idx] = [None]
                chain = self.player.weapon_chain[self.selected_chain_idx]
                print(f"Initialized chain {self.selected_chain_idx + 1} with one empty slot")

            for slot_idx, weapon in enumerate(chain):
                slot_rect = pygame.Rect(x_offset, y_offset, 100, 100)
                pygame.draw.rect(self.screen, (0, 255, 0), slot_rect, 2)
                weapon_text = font.render(weapon.name if weapon else "Empty", True, (255, 255, 255))
                self.screen.blit(weapon_text, (slot_rect.x + 10, slot_rect.y + 10))
                plus_rect = pygame.Rect(slot_rect.right + 5, y_offset + 30, 30, 30)
                pygame.draw.rect(self.screen, (0, 255, 0), plus_rect, 2)
                self.screen.blit(font.render("+", True, (255, 255, 255)), (plus_rect.x + 10, plus_rect.y + 5))
                minus_rect = pygame.Rect(slot_rect.right + 40, y_offset + 30, 30, 30)
                pygame.draw.rect(self.screen, (255, 0, 0), minus_rect, 2)
                self.screen.blit(font.render("-", True, (255, 255, 255)), (minus_rect.x + 10, minus_rect.y + 5))
                chain_rects.append((slot_rect, plus_rect, minus_rect))
                y_offset += 120

            self.inventory_rects[self.selected_chain_idx] = chain_rects

            # Draw player weapons on the right
            y_offset = 100
            weapon_list_x = SCREEN_WIDTH // 2 + 50
            title = font.render("Player Weapons", True, (255, 255, 255))
            self.screen.blit(title, (weapon_list_x, y_offset))
            y_offset += 40
            for weapon in self.player.weapons:
                text = font.render(f"{weapon.name} (Energy: {weapon.energy_cost})", True, (255, 255, 255))
                self.screen.blit(text, (weapon_list_x, y_offset))
                y_offset += 40

        elif self.inventory_mode == "weapon_selection":
            self.inventory_rects = []
            y_offset = 100
            chain = self.player.weapon_chain[self.selected_chain_idx] if self.selected_chain_idx < len(self.player.weapon_chain) else []
            used_weapons = set(weapon for weapon in chain if weapon is not None)
            available_weapons = [weapon for weapon in self.player.weapons if weapon not in used_weapons]
            title = font.render(f"Select Weapon for Slot {self.selected_weapon_slot_idx + 1}", True, (255, 255, 255))
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, y_offset))
            y_offset += 40

            for weapon_idx, weapon in enumerate(available_weapons):
                text = font.render(f"{weapon.name} (Energy: {weapon.energy_cost}, Fire Rate: {weapon.fire_rate}s)", True, (255, 255, 255))
                rect = pygame.Rect(SCREEN_WIDTH // 2 - text.get_width() // 2, y_offset, text.get_width(), text.get_height())
                self.screen.blit(text, (rect.x, rect.y))
                self.inventory_rects.append(rect)
                y_offset += 40

            if not available_weapons:
                error_text = font.render("No available weapons!", True, (255, 0, 0))
                self.screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, y_offset))

            # Debug: Print rectangle positions
            print(f"Weapon selection rectangles: {[(rect.x, rect.y, rect.width, rect.height) for rect in self.inventory_rects]}")

        pygame.display.flip()
    
    
    def _draw_menu_options(self, options, selected_idx, font_size=48):
        """Draw a menu with selectable options."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, font_size)
        for i, option in enumerate(options):
            color = (255, 255, 0) if i == selected_idx else (255, 255, 255)
            text = font.render(option, True, color)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200 + i * 50))

    def draw(self):
        """Main draw method to handle all game states."""
        self.screen.fill((0, 0, 0))
        state_draw_methods = {
            "menu": self.draw_menu,
            "lobby": self.draw_lobby,
            "npc_menu": self.draw_npc_menu,
            "select_skill": self.draw_skill_selection,
            "select_weapons": self.draw_weapon_selection,
            "playing": self.draw_playing,
            "inventory": self.draw_inventory,
            "win": self.draw_win
        }
        state_draw_methods[self.state]()

    def _draw_game_world(self):
        """Draw the dungeon, entities, health bars, and UI elements."""
        view_left = max(0, int(-self.camera_offset[0] // TILE_SIZE - 1))
        view_right = min(self.dungeon.grid_width, int((-self.camera_offset[0] + SCREEN_WIDTH) // TILE_SIZE + 1))
        view_top = max(0, int(-self.camera_offset[1] // TILE_SIZE - 1))
        view_bottom = min(self.dungeon.grid_height, int((-self.camera_offset[1] + SCREEN_HEIGHT) // TILE_SIZE + 1))

        for row in range(view_top, view_bottom):
            for col in range(view_left, view_right):
                x = col * TILE_SIZE + self.camera_offset[0]
                y = row * TILE_SIZE + self.camera_offset[1]
                if row < 0 or row >= self.dungeon.grid_height or col < 0 or col >= self.dungeon.grid_width:
                    continue
                else:
                    tile = self.dungeon.dungeon_tiles[row][col]
                    self.draw_3d_walls(row, col, x, y, tile)

        self.screen.blit(self.player.image, (self.player.rect.x + self.camera_offset[0],
                                            self.player.rect.y + self.camera_offset[1]))
        self.player.draw_health_bar(self.screen, self.camera_offset)

        for npc in self.npc_group:
            npc.draw(self.screen, self.camera_offset)
            if npc.can_interact(self.player.pos):
                font = pygame.font.SysFont(None, 24)
                prompt = font.render("Press E to interact", True, (255, 255, 255))
                self.screen.blit(prompt, (npc.rect.centerx + self.camera_offset[0] - prompt.get_width() // 2,
                                        npc.rect.top + self.camera_offset[1] - 20))

        for enemy in self.enemy_group:
            if enemy.health > 0 and enemy.pos[0] + self.camera_offset[0] >= 0 and enemy.pos[1] + self.camera_offset[1] >= 0:
                self.screen.blit(enemy.image, (enemy.rect.x + self.camera_offset[0],
                                              enemy.rect.y + self.camera_offset[1]))
                enemy.draw_health_bar(self.screen, self.camera_offset)

        for bullet in self.player_bullet_group:
            self.screen.blit(bullet.image, (bullet.rect.x + self.camera_offset[0],
                                         bullet.rect.y + self.camera_offset[1]))
        for bullet in self.enemy_bullet_group:
            self.screen.blit(bullet.image, (bullet.rect.x + self.camera_offset[0],
                                         bullet.rect.y + self.camera_offset[1]))

        for damage_text in self.damage_text_group:
            self.screen.blit(damage_text.image, (damage_text.rect.x + self.camera_offset[0],
                                               damage_text.rect.y + self.camera_offset[1]))

        if self.fog_surface:
            self.screen.blit(self.fog_surface, (0, 0))

        for row in range(view_top, view_bottom):
            for col in range(view_left, view_right):
                x = col * TILE_SIZE + self.camera_offset[0]
                y = row * TILE_SIZE + self.camera_offset[1]
                if row < 0 or row >= self.dungeon.grid_height or col < 0 or col >= self.dungeon.grid_width:
                    continue
                else:
                    tile = self.dungeon.dungeon_tiles[row][col]
                    if tile == 'Border_wall':
                        self.draw_3d_walls(row, col, x, y, tile, True)

        self._draw_hud()

        self.draw_minimap()

    def draw_menu(self):
        """Draw the main menu with hover and click support."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 48)
        self.menu_rects = []
        mouse_pos = pygame.mouse.get_pos()

        for i, option in enumerate(self.menu_options):
            hovered = False
            for j, rect in enumerate(self.menu_rects):
                if rect.collidepoint(mouse_pos) and i == j:
                    hovered = True
                    break
            color = (255, 255, 0) if i == self.selected_menu_option or hovered else (255, 255, 255)
            text = font.render(option, True, color)
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            y = 200 + i * 60
            self.screen.blit(text, (x, y))
            rect = pygame.Rect(x, y, text.get_width(), text.get_height())
            self.menu_rects.append(rect)
            if hovered:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)

        pygame.display.flip()

    def draw_npc_menu(self):
        """Draw the NPC interaction menu with hover and click support."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 48)
        self.npc_menu_rects = []
        mouse_pos = pygame.mouse.get_pos()

        for i, option in enumerate(self.npc_menu_options):
            hovered = False
            for j, rect in enumerate(self.npc_menu_rects):
                if rect.collidepoint(mouse_pos) and i == j:
                    hovered = True
                    break
            color = (255, 255, 0) if i == self.selected_npc_menu_option or hovered else (255, 255, 255)
            text = font.render(option, True, color)
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            y = 200 + i * 60
            self.screen.blit(text, (x, y))
            rect = pygame.Rect(x, y, text.get_width(), text.get_height())
            self.npc_menu_rects.append(rect)
            if hovered or i == self.selected_npc_menu_option:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)

        pygame.display.flip()

    def draw_skill_selection(self):
        """Draw the skill selection interface with hover, click, and scroll support."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
        title = font.render("Select a Skill (Click or ENTER to select/deselect, Scroll or UP/DOWN to navigate, ESC to cancel)", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 36))

        self.skill_rects = []
        mouse_pos = pygame.mouse.get_pos()

        if not self.skills_library:
            error_text = font.render("No skills available!", True, (255, 0, 0))
            self.screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 100))
        else:
            for i, skill in enumerate(self.skills_library):
                is_selected = (skill, 'right_click') in self.selected_skills
                hovered = False
                for j, rect in enumerate(self.skill_rects):
                    if rect.collidepoint(mouse_pos) and i == j:
                        hovered = True
                        break
                color = (0, 255, 0) if is_selected else (255, 255, 0) if skill == self.selected_skill or hovered else (255, 255, 255)
                text = font.render(f"{skill.name} (Cooldown: {skill.cooldown}s)", True, color)
                x = SCREEN_WIDTH // 2 - text.get_width() // 2
                y = 100 + i * 40
                self.screen.blit(text, (x, y))
                rect = pygame.Rect(x, y, text.get_width(), text.get_height())
                self.skill_rects.append(rect)
                if is_selected:
                    pygame.draw.rect(self.screen, (0, 255, 0), rect, 2)
                elif hovered or skill == self.selected_skill:
                    pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)

        count_text = font.render(f"Selected Skills: {len(self.selected_skills)}/{self.player.max_skills}", True, (255, 255, 255))
        self.screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 400))
        pygame.display.flip()

    def draw_weapon_selection(self):
        """Draw the weapon selection interface with hover, click, and scroll support."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
        max_weapons = self.player.max_weapons if self.player else MAX_WEAPONS_DEFAULT
        title = font.render(f"Select Weapons (Click or ENTER to select/deselect, Scroll or UP/DOWN to navigate, SPACE to confirm, ESC to cancel)", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 36))

        self.weapon_rects = []
        mouse_pos = pygame.mouse.get_pos()

        if not self.weapons_library:
            error_text = font.render("No weapons available!", True, (255, 0, 0))
            self.screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 100))
        else:
            for i, weapon in enumerate(self.weapons_library):
                count = self.selected_weapons.count(weapon)
                is_selected = weapon in self.selected_weapons
                hovered = False
                for j, rect in enumerate(self.weapon_rects):
                    if rect.collidepoint(mouse_pos) and i == j:
                        hovered = True
                        break
                color = (0, 255, 0) if is_selected else (255, 255, 0) if hovered else (255, 255, 255)
                text = font.render(f"{weapon.name} (Selected: {count}, Energy Cost: {weapon.energy_cost}, Fire Rate: {weapon.fire_rate}s)", True, color)
                x = SCREEN_WIDTH // 2 - text.get_width() // 2
                y = 100 + i * 40
                self.screen.blit(text, (x, y))
                rect = pygame.Rect(x, y, text.get_width(), text.get_height())
                self.weapon_rects.append(rect)
                if is_selected:
                    pygame.draw.rect(self.screen, (0, 255, 0), rect, 2)
                elif hovered:
                    pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)

        count_text = font.render(f"Selected: {len(self.selected_weapons)}/{max_weapons}", True, (255, 255, 255))
        self.screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 400))
        pygame.display.flip()

    def draw_lobby(self):
        """Draw the lobby state."""
        self._draw_game_world()
        pygame.display.flip()

    def draw_playing(self):
        """Draw the playing state."""
        self._draw_game_world()
        pygame.display.flip()

    def draw_win(self):
        """Draw the victory screen."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 48)
        win_text = font.render("Victory! You cleared all dungeons!", True, (255, 255, 0))
        self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                                  SCREEN_HEIGHT // 2 - win_text.get_height() // 2))
        pygame.display.flip()