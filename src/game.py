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
        self.vision_radius = 15
        self.fog_edge_thickness = 3
        self.fog_surface = None
        self.last_player_pos = None
        self.last_vision_radius = None
        self.dungeon_clear_count = 0
        self.dungeon_clear_goal = 5

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
        """Set up the lobby room with player and NPC."""
        self.dungeon.initialize_lobby()
        self.current_room_id = 0
        spawn_room = self.dungeon.get_room(self.current_room_id)
        center_x, center_y = self._get_room_center(spawn_room)
        
        self.player = Player(pos=(center_x, center_y), game=self)
        self.player.skills = [(skill, key) for skill, key in self.selected_skills]
        self.player.weapons = self.selected_weapons
        
        npc_pos = (center_x + 2 * TILE_SIZE, center_y)
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
        self._generate_new_enemies()

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

        self.player.skills = [(skill, key) for skill, key in self.selected_skills]
        for skill, _ in self.player.skills:
            if skill.cooldown == 0:
                skill.use(self.player, self, self.current_time)
        self.player.weapons = self.selected_weapons
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

    def _generate_new_enemies(self):
        """Clear existing enemies and spawn new ones randomly."""
        self.enemy_group.empty()
        self.enemy_bullet_group.empty()
        self.player_bullet_group.empty()
        
        num_enemies = max(1, len(self.dungeon.rooms) // 2)
        for _ in range(num_enemies):
            room = random.choice(self.dungeon.rooms)
            enemy_pos = (
                room.x * TILE_SIZE + random.randint(0, room.width * TILE_SIZE - TILE_SIZE),
                room.y * TILE_SIZE + random.randint(0, room.height * TILE_SIZE - TILE_SIZE)
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
        colors = {
            'Room_floor': ROOM_FLOOR_COLOR,
            'Border_wall': DARK_RED if is_wall else BORDER_WALL_COLOR,
            'Bridge_floor': BRIDGE_FLOOR_COLOR,
            'End_room_floor': END_ROOM_FLOOR_COLAR,
            'End_room_portal': END_ROOM_PROTAL_COLOR,
        }
        return colors.get(tile, OUTSIDE_COLOR)

    def draw_3d_walls(self, row, col, x, y, tile, is_wall=False):
        """Draw a tile with 3D wall effect if applicable."""
        color = self._get_tile_color(tile, is_wall)
        if is_wall and tile == 'Border_wall':
            wall_shift = int(TILE_SIZE * 0.65)
            wall_height = TILE_SIZE
            pygame.draw.rect(self.screen, DARK_RED, (x, y, TILE_SIZE, wall_height))
            pygame.draw.rect(self.screen, color, (x, y - wall_shift, TILE_SIZE, TILE_SIZE))
        elif not is_wall and tile != 'Border_wall':
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
                    pygame.draw.rect(minimap_surface, BRIDGE_FLOOR_COLOR, (minimap_x, minimap_y, 1, 1))

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
        length = math.sqrt(direction[0]**2 + direction[1]**2)
        if length > 0:
            direction = (direction[0] / length, direction[1] / length)
        if pygame.mouse.get_pressed()[0]:
            bullet = self.player.fire(direction, self.current_time)
            if bullet:
                self.player_bullet_group.add(bullet)

    def _handle_skill_activation(self, event):
        """Activate a skill based on key press."""
        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                        pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0):
            key = str(event.key - pygame.K_0) if event.key == pygame.K_0 else str(event.key - pygame.K_1 + 1)
            for skill, bound_key in self.player.skills:
                if bound_key == key and skill.can_use(self.player, self.current_time):
                    skill.use(self.player, self, self.current_time)
                    print(f"Skill {skill.name} used with key {key}")

    def _update_bullets(self, dt: float):
        """Update bullets and handle collisions."""
        for bullet in self.player_bullet_group.copy():
            if not bullet.update(dt):
                self.player_bullet_group.remove(bullet)
            else:
                for enemy in self.enemy_group:
                    if bullet.rect.colliderect(enemy.rect):
                        enemy.take_damage(bullet.damage)
                        self.player_bullet_group.remove(bullet)
                        break

        for bullet in self.enemy_bullet_group.copy():
            if not bullet.update(dt):
                self.enemy_bullet_group.remove(bullet)
            elif bullet.shooter != self.player and self.player.invulnerable <= 0 and bullet.rect.colliderect(self.player.rect):
                self.player.take_damage(bullet.damage)
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

    def _check_dungeon_completion(self):
        """Check if player reached the end portal and handle dungeon progression."""
        if self.dungeon.get_tile_at(self.player.pos) == 'End_room_portal':
            self.dungeon_clear_count += 1
            if self.dungeon_clear_count >= self.dungeon_clear_goal:
                self.state = "win"
            else:
                print(f"已通過 {self.dungeon_clear_count} 次地牢，進入下一層！")
                self._start_new_dungeon()
                self._generate_new_enemies()

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
        return True

    def _update_menu(self, events):
        """Handle menu navigation and selection."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_menu_option = (self.selected_menu_option - 1) % len(self.menu_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_menu_option = (self.selected_menu_option + 1) % len(self.menu_options)
                elif event.key == pygame.K_RETURN:
                    if self.menu_options[self.selected_menu_option] == "Enter Lobby":
                        if self.skills_library:
                            self.state = "lobby"
                            self.initialize_lobby()
                        else:
                            print("No skills available, cannot start game")
                    else:
                        return False
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
                elif event.key == pygame.K_c:
                    self.player.current_weapon_idx = (self.player.current_weapon_idx + 1) % len(self.player.weapons) if self.player.weapons else 0
                else:
                    self._handle_skill_activation(event)

        self._handle_player_firing(dt)
        self._update_bullets(dt)
        self._update_enemies(dt)
        self.update_camera(dt)
        self._update_fog_map_from_player()
        self.update_fog_surface()
        self.last_player_pos = (self.player.pos[0], self.player.pos[1])
        self.last_vision_radius = self.player.vision_radius
        return True

    def _update_npc_menu(self, events):
        """Handle NPC menu navigation and selection."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_npc_menu_option = (self.selected_npc_menu_option - 1) % len(self.npc_menu_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_npc_menu_option = (self.selected_npc_menu_option + 1) % len(self.npc_menu_options)
                elif event.key == pygame.K_RETURN:
                    if self.npc_menu_options[self.selected_npc_menu_option] == "Select Skills":
                        if self.skills_library:
                            self.state = "select_skill"
                            self.selected_skill = self.skills_library[0]
                        else:
                            print("No skills available")
                    elif self.npc_menu_options[self.selected_npc_menu_option] == "Select Weapons":
                        self.state = "select_weapons"
                    elif self.npc_menu_options[self.selected_npc_menu_option] == "Start Game":
                        if self.selected_weapons and self.selected_skills:
                            self.start_game()
                        else:
                            print("Must select at least one skill and one weapon")
                elif event.key == pygame.K_ESCAPE:
                    self.state = "lobby"
                    self.player.skills = [(skill, key) for skill, key in self.selected_skills]
        return True

    def _update_skill_selection(self, events):
        """Handle skill selection and key binding."""
        if not self.skills_library:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "npc_menu"
                    self.selected_skill = None
            return True

        for event in events:
            if event.type == pygame.KEYDOWN:
                current_idx = self.skills_library.index(self.selected_skill) if self.selected_skill in self.skills_library else 0
                if event.key == pygame.K_UP:
                    current_idx = (current_idx - 1) % len(self.skills_library)
                    self.selected_skill = self.skills_library[current_idx]
                elif event.key == pygame.K_DOWN:
                    current_idx = (current_idx + 1) % len(self.skills_library)
                    self.selected_skill = self.skills_library[current_idx]
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                                 pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0):
                    if len(self.selected_skills) < 10:
                        key = str(event.key - pygame.K_0) if event.key == pygame.K_0 else str(event.key - pygame.K_1 + 1)
                        for i, (skill, bound_key) in enumerate(self.selected_skills):
                            if bound_key == key:
                                self.selected_skills[i] = (self.selected_skill, key)
                                print(f"Skill {self.selected_skill.name} rebound to key {key}")
                                break
                        else:
                            self.selected_skills.append((self.selected_skill, key))
                            print(f"Skill {self.selected_skill.name} bound to key {key}")
                    else:
                        print("Maximum 10 skills can be bound")
                elif event.key == pygame.K_BACKSPACE:
                    for i, (skill, _) in enumerate(self.selected_skills):
                        if skill == self.selected_skill:
                            self.selected_skills.pop(i)
                            print(f"Skill {skill.name} unbound")
                            break
                elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.state = "npc_menu"
        return True

    def _update_weapon_selection(self, events):
        """Handle weapon selection and removal."""
        max_weapons = self.player.max_weapons if self.player else MAX_WEAPONS_DEFAULT
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    idx = event.key - pygame.K_1
                    if idx < len(self.weapons_library) and len(self.selected_weapons) < max_weapons:
                        self.selected_weapons.append(self.weapons_library[idx])
                        print(f"Selected weapon: {self.weapons_library[idx].name}")
                    else:
                        print("Invalid weapon selection or max weapons reached")
                elif event.key == pygame.K_BACKSPACE and self.selected_weapons:
                    removed_weapon = self.selected_weapons.pop()
                    print(f"Removed weapon: {removed_weapon.name}")
                elif event.key == pygame.K_RETURN:
                    if self.selected_weapons:
                        self.player.weapons = self.selected_weapons
                        self.state = "npc_menu"
                    else:
                        print("At least one weapon must be selected")
                elif event.key == pygame.K_ESCAPE:
                    self.state = "npc_menu"
        return True

    def _update_playing(self, dt: float, events):
        """Update gameplay state with player actions and game logic."""
        self._handle_player_movement(dt)
        self.player.update(dt, self.current_time)
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    self.player.current_weapon_idx = (self.player.current_weapon_idx + 1) % len(self.player.weapons)
                elif event.key == pygame.K_r:
                    if self.dungeon_clear_count >= self.dungeon_clear_goal:
                        self.state = "win"
                    else:
                        print(f"已通過 {self.dungeon_clear_count} 次地牢，進入下一層！")
                        self._start_new_dungeon()
                        self._generate_new_enemies()
                else:
                    self._handle_skill_activation(event)

        self._handle_player_firing(dt)
        self._update_bullets(dt)
        self._update_enemies(dt)
        self.update_camera(dt)
        self._update_fog_map_from_player()
        self.update_fog_surface()
        self.last_player_pos = (self.player.pos[0], self.player.pos[1])
        self.last_vision_radius = self.player.vision_radius
        self._check_dungeon_completion()
        return True

    def _draw_menu_options(self, options, selected_idx, font_size=48):
        """Draw a menu with selectable options."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, font_size)
        for i, option in enumerate(options):
            color = (255, 255, 0) if i == selected_idx else (255, 255, 255)
            text = font.render(option, True, color)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200 + i * 50))

    def draw_menu(self):
        """Draw the main menu."""
        self._draw_menu_options(self.menu_options, self.selected_menu_option)
        pygame.display.flip()

    def draw_npc_menu(self):
        """Draw the NPC interaction menu."""
        self._draw_menu_options(self.npc_menu_options, self.selected_npc_menu_option)
        pygame.display.flip()

    def draw_skill_selection(self):
        """Draw the skill selection interface."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
        title = font.render("Select a Skill and Bind to Key (1-9, 0) or ENTER to confirm, ESC to cancel", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 36))

        if not self.skills_library:
            error_text = font.render("No skills available!", True, (255, 0, 0))
            self.screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 100))
        else:
            for i, skill in enumerate(self.skills_library):
                bound_key = next((k for s, k in self.selected_skills if s == skill), None)
                color = (255, 255, 0) if skill == self.selected_skill else (255, 255, 255)
                text = font.render(f"{skill.name} (Cooldown: {skill.cooldown}s, Key: {bound_key if bound_key else 'None'})", True, color)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 100 + i * 40))

        count_text = font.render(f"Selected Skills: {len(self.selected_skills)}/10", True, (255, 255, 255))
        self.screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 400))
        pygame.display.flip()

    def draw_weapon_selection(self):
        """Draw the weapon selection interface."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
        max_weapons = self.player.max_weapons if self.player else MAX_WEAPONS_DEFAULT
        title = font.render(f"Select Weapons (Max: {max_weapons}, 1-4 to select, BACKSPACE to remove, ENTER to start, ESC to cancel)", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 36))

        if not self.weapons_library:
            error_text = font.render("No weapons available!", True, (255, 0, 0))
            self.screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 100))
        else:
            for i, weapon in enumerate(self.weapons_library):
                count = self.selected_weapons.count(weapon)
                text = font.render(f"{weapon.name} (Selected: {count}, Energy Cost: {weapon.energy_cost}, Fire Rate: {weapon.fire_rate}s)", True, (255, 255, 255))
                self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 100 + i * 40))

        count_text = font.render(f"Selected: {len(self.selected_weapons)}/{max_weapons}", True, (255, 255, 255))
        self.screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 400))
        pygame.display.flip()

    def _draw_game_world(self):
        """Draw the dungeon, entities, and UI elements."""
        view_left = max(0, int(-self.camera_offset[0] // TILE_SIZE - 1))
        view_right = min(self.dungeon.grid_width, int((-self.camera_offset[0] + SCREEN_WIDTH) // TILE_SIZE + 1))
        view_top = max(0, int(-self.camera_offset[1] // TILE_SIZE - 1))
        view_bottom = min(self.dungeon.grid_height, int((-self.camera_offset[1] + SCREEN_HEIGHT) // TILE_SIZE + 1))

        # Draw floor tiles
        for row in range(view_top, view_bottom):
            for col in range(view_left, view_right):
                x = col * TILE_SIZE + self.camera_offset[0]
                y = row * TILE_SIZE + self.camera_offset[1]
                try:
                    tile = self.dungeon.dungeon_tiles[row][col]
                    self.draw_3d_walls(row, col, x, y, tile)
                except IndexError:
                    continue

        # Draw player
        self.screen.blit(self.player.image, (self.player.rect.x + self.camera_offset[0], 
                                          self.player.rect.y + self.camera_offset[1]))

        # Draw NPCs (in lobby)
        if self.state == "lobby":
            for npc in self.npc_group:
                npc.draw(self.screen, self.camera_offset)
                if npc.can_interact(self.player.pos):
                    font = pygame.font.SysFont(None, 24)
                    prompt = font.render("Press E to interact", True, (255, 255, 255))
                    self.screen.blit(prompt, (npc.rect.centerx + self.camera_offset[0] - prompt.get_width() // 2, 
                                            npc.rect.top + self.camera_offset[1] - 20))

        # Draw enemies
        for enemy in self.enemy_group:
            if enemy.health > 0 and enemy.pos[0] + self.camera_offset[0] >= 0 and enemy.pos[1] + self.camera_offset[1] >= 0:
                self.screen.blit(enemy.image, (enemy.rect.x + self.camera_offset[0], 
                                            enemy.rect.y + self.camera_offset[1]))

        # Draw bullets
        for bullet in self.player_bullet_group:
            self.screen.blit(bullet.image, (bullet.rect.x + self.camera_offset[0], 
                                         bullet.rect.y + self.camera_offset[1]))
        for bullet in self.enemy_bullet_group:
            self.screen.blit(bullet.image, (bullet.rect.x + self.camera_offset[0], 
                                         bullet.rect.y + self.camera_offset[1]))

        # Draw fog
        if self.fog_surface:
            self.screen.blit(self.fog_surface, (0, 0))

        # Draw walls
        for row in range(view_top, view_bottom):
            for col in range(view_left, view_right):
                x = col * TILE_SIZE + self.camera_offset[0]
                y = row * TILE_SIZE + self.camera_offset[1]
                try:
                    tile = self.dungeon.dungeon_tiles[row][col]
                    if tile == 'Border_wall':
                        self.draw_3d_walls(row, col, x, y, tile, True)
                except IndexError:
                    continue

        # Draw UI
        self._draw_hud()

        # Draw minimap
        self.draw_minimap()

    def _draw_hud(self):
        """Draw heads-up display with player stats and progress."""
        font = pygame.font.SysFont(None, 36)
        self.screen.blit(font.render(f"Health: {self.player.health}/{self.player.max_health}", True, (255, 255, 255)), (10, 10))
        self.screen.blit(font.render(f"Energy: {int(self.player.energy)}/{int(self.player.max_energy)}", True, (255, 255, 255)), (10, 50))
        
        if self.player.weapons:
            weapon = self.player.weapons[self.player.current_weapon_idx]
            self.screen.blit(font.render(f"{weapon.name}: {weapon.energy_cost} Energy/Shot", True, (255, 255, 255)), (10, 90))

        y_offset = 130
        for skill, key in self.player.skills:
            self.screen.blit(font.render(f"Skill {key}: {skill.name}", True, (255, 255, 255)), (10, y_offset))
            if skill.cooldown > 0:
                cooldown = max(0, skill.cooldown - (self.current_time - skill.last_used))
                self.screen.blit(font.render(f"CD: {cooldown:.1f}s", True, (255, 255, 255)), (150, y_offset))
            y_offset += 40

        if self.state == "playing":
            progress_text = font.render(f"Dungeon: {self.dungeon_clear_count+1}/{self.dungeon_clear_goal}", True, (255, 255, 0))
            self.screen.blit(progress_text, (10, y_offset))

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
            "win": self.draw_win
        }
        state_draw_methods[self.state]()