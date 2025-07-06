# src/game.py
import pygame
import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from src.weapons.weapon import *
from src.weapons.weapon_library import WEAPON_LIBRARY
from src.skills.skill import *
from src.skills.skill_library import SKILL_LIBRARY
from src.dungeon.dungeon import *
from src.config import *
from src.character.character import *
from src.enemy.basic_enemy import BasicEnemy

class Game:
    def __init__(self, screen, pygame_clock):
        self.screen = screen
        self.clock = pygame_clock
        self.dungeon = Dungeon()
        self.dungeon.game = self
        self.player = None
        self.player_bullet_group = pygame.sprite.Group()  # Player bullets
        self.enemy_bullet_group = pygame.sprite.Group()  # Enemy bullets
        self.enemy_group = pygame.sprite.Group()
        self.current_time = 0.0
        self.state = "menu"
        self.selected_skill = None
        self.selected_weapons = []
        self.menu_options = ["Start Game", "Exit"]
        self.selected_menu_option = 0
        self.camera_lerp_factor = 1.5
        self.current_room_id = 0
        self.skills_library = SKILL_LIBRARY
        self.weapons_library = WEAPON_LIBRARY
        self.camera_offset = [0, 0]
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
        # 2.5D background setup
        self.background_layers = [
            {"color": (50, 50, 50), "scale": 0.5, "offset": 0.2},  # Distant layer
            {"color": (80, 80, 80), "scale": 0.7, "offset": 0.4},  # Mid layer
            {"color": (110, 110, 110), "scale": 0.9, "offset": 0.6}  # Near layer
        ]

    def draw_menu(self):
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 48)
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_menu_option else (255, 255, 255)
            text = font.render(option, True, color)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200 + i * 50))
        pygame.display.flip()

    def draw_skill_selection(self):
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
        title = font.render("Select a Skill (UP/DOWN to navigate, ENTER to confirm, ESC to cancel)", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 36))
        if not self.skills_library:
            error_text = font.render("No skills available!", True, (255, 0, 0))
            self.screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 100))
        else:
            for i, skill in enumerate(self.skills_library):
                color = (255, 255, 0) if skill == self.selected_skill else (255, 255, 255)
                text = font.render(f"{skill.name} (Cooldown: {skill.cooldown}s)", True, color)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 100 + i * 40))
        pygame.display.flip()

    def draw_weapon_selection(self):
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
                text = font.render(f"{weapon.name} (Selected: {count}, Ammo: {weapon.max_ammo if not weapon.is_melee else '∞'}, Fire Rate: {weapon.fire_rate}s)", True, (255, 255, 255))
                self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 100 + i * 40))
        selected_count = len(self.selected_weapons)
        count_text = font.render(f"Selected: {selected_count}/{max_weapons}", True, (255, 255, 255))
        self.screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 400))
        pygame.display.flip()

    def start_game(self):
        self.dungeon_clear_count = 0
        self._start_new_dungeon()
        self._generate_new_enemies()

    def _start_new_dungeon(self):
        self.dungeon.initialize_dungeon()
        for room in self.dungeon.rooms:
            if room.room_type == RoomType.START:
                self.current_room_id = room.id
                break
        spawn_room = self.dungeon.get_room(self.current_room_id)
        center_tile_x = int(spawn_room.x + spawn_room.width // 2)
        center_tile_y = int(spawn_room.y + spawn_room.height // 2)
        center_x = center_tile_x * TILE_SIZE
        center_y = center_tile_y * TILE_SIZE
        if not self.player:
            self.player = Player(pos=(center_x, center_y), game=self)
        else:
            self.player.pos = (center_x, center_y)
            self.player.rect.x = center_x
            self.player.rect.y = center_y
            self.player.health = self.player.max_health
        self.player.skill = self.selected_skill
        if self.player.skill and self.player.skill.cooldown == 0:
            self.player.skill.use(self.player, self, self.current_time)
        self.player.weapons = self.selected_weapons
        self.state = "playing"
        self.camera_offset = [-(self.player.pos[0] - SCREEN_WIDTH // 2),
                              -(self.player.pos[1] - SCREEN_HEIGHT // 2)]
        self.minimap_width = int(self.dungeon.grid_width * self.minimap_scale)
        self.minimap_height = int(self.dungeon.grid_height * self.minimap_scale)
        self.minimap_offset = (SCREEN_WIDTH - self.minimap_width - 10, 10)
        self.fog_map = [[False for _ in range(self.dungeon.grid_width)] for _ in range(self.dungeon.grid_height)]
        self.update_fog_map(center_tile_x, center_tile_y)
        self.last_player_pos = None
        self.last_vision_radius = None
        
    def _generate_new_enemies(self):
        """Generate new enemies based on the number of rooms and difficulty."""
        if self.enemy_group:
            self.enemy_group.empty()
        if self.enemy_bullet_group:
            self.enemy_bullet_group.empty()
        if self.player_bullet_group:
            self.player_bullet_group.empty()
        num_enemies = max(1, len(self.dungeon.rooms) // 2)
        for _ in range(num_enemies):
            room = random.choice(self.dungeon.rooms)
            enemy = BasicEnemy(pos=(room.x * TILE_SIZE + random.randint(0, room.width * TILE_SIZE - TILE_SIZE),
                                    room.y * TILE_SIZE + random.randint(0, room.height * TILE_SIZE - TILE_SIZE)),
                                game=self)
            self.enemy_group.add(enemy)

    def update_fog_map(self, tile_x: int, tile_y: int):
        """Update fog map, marking explored tiles (for minimap)."""
        for y in range(max(0, tile_y - self.vision_radius), min(self.dungeon.grid_height, tile_y + self.vision_radius + 1)):
            for x in range(max(0, tile_x - self.vision_radius), min(self.dungeon.grid_width, tile_x + self.vision_radius + 1)):
                distance = math.sqrt((x - tile_x) ** 2 + (y - tile_y) ** 2)
                try:
                    if distance <= self.vision_radius:
                        self.fog_map[y][x] = True  # Mark as explored
                except:
                    pass

    def draw_3d_walls(self, row, col, x, y, tile, wall=False):
        """Draw walls with a 3D effect by shifting original tile up and adding a dark red face."""
        color = {
            'Room_floor': ROOM_FLOOR_COLOR,
            'Border_wall': BORDER_WALL_COLOR,
            'Bridge_floor': BRIDGE_FLOOR_COLOR,
            'End_room_floor': END_ROOM_FLOOR_COLAR,
            'End_room_portal': END_ROOM_PROTAL_COLOR,
        }.get(tile, OUTSIDE_COLOR)
        if wall:
            if tile == 'Border_wall':
                # Shift wall tile upward
                wall_shift = int(TILE_SIZE * 0.65)  # Shift up by half tile size
                wall_height = TILE_SIZE  # Height of the dark red face
                # Draw original wall tile shifted up
                pygame.draw.rect(self.screen, color, (x, y - wall_shift, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(self.screen, (255, 255, 255), (x, y - wall_shift, TILE_SIZE, TILE_SIZE), 1)
            else:
                pass
        else:
            if tile == 'Border_wall':
                # Shift wall tile upward
                wall_shift = int(TILE_SIZE * 0.65)  # Shift up by half tile size
                wall_height = TILE_SIZE  # Height of the dark red face
                # Draw dark red wall face below
                pygame.draw.rect(self.screen, DARK_RED, (x, y, TILE_SIZE, wall_height))
                pygame.draw.rect(self.screen, (255, 255, 255), (x, y, TILE_SIZE, wall_height), 1)
            else:
                # Draw flat tiles for non-walls
                pygame.draw.rect(self.screen, color, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(self.screen, (255, 255, 255), (x, y, TILE_SIZE, TILE_SIZE), 1)

    def draw_minimap(self):
        minimap_surface = pygame.Surface((self.minimap_width, self.minimap_height))
        minimap_surface.fill((0, 0, 0))
        for room in self.dungeon.rooms:
            for row in range(int(room.height)):
                for col in range(int(room.width)):
                    grid_x = int(room.x + col)
                    grid_y = int(room.y + row)
                    if 0 <= grid_y < self.dungeon.grid_height and 0 <= grid_x < self.dungeon.grid_width:
                        if self.fog_map[grid_y][grid_x]:
                            minimap_x = int(grid_x * self.minimap_scale)
                            minimap_y = int(grid_y * self.minimap_scale)
                            tile = room.tiles[row][col]
                            color = {
                                'Room_floor': ROOM_FLOOR_COLOR,
                                'Border_wall': BORDER_WALL_COLOR,
                                'End_room_floor': END_ROOM_FLOOR_COLAR,
                                'End_room_portal': END_ROOM_PROTAL_COLOR,
                            }.get(tile, OUTSIDE_COLOR)
                            pygame.draw.rect(minimap_surface, color, (minimap_x, minimap_y, 1, 1))
        for y in range(self.dungeon.grid_height):
            for x in range(self.dungeon.grid_width):
                try:
                    if self.fog_map[y][x] and self.dungeon.dungeon_tiles[y][x] == 'Bridge_floor':
                        minimap_x = int(x * self.minimap_scale)
                        minimap_y = int(y * self.minimap_scale)
                        pygame.draw.rect(minimap_surface, BRIDGE_FLOOR_COLOR, (minimap_x, minimap_y, 1, 1))
                except:
                    pass
        if self.player:
            player_minimap_x = int(self.player.pos[0] / TILE_SIZE * self.minimap_scale)
            player_minimap_y = int(self.player.pos[1] / TILE_SIZE * self.minimap_scale)
            pygame.draw.circle(minimap_surface, (0, 255, 0), (player_minimap_x, player_minimap_y), 3)
        self.screen.blit(minimap_surface, self.minimap_offset)

    def update(self, dt: float):
        self.current_time += dt * self.time_scale
        if self.player and self.player.invulnerable > 0:
            self.player.invulnerable -= dt
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT and self.time_scale < 1.0:
                self.time_scale = 1.0
                pygame.time.set_timer(pygame.USEREVENT, 0)
        if self.state == "menu":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_menu_option = (self.selected_menu_option - 1) % len(self.menu_options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_menu_option = (self.selected_menu_option + 1) % len(self.menu_options)
                    elif event.key == pygame.K_RETURN:
                        if self.menu_options[self.selected_menu_option] == "Start Game":
                            if self.skills_library:
                                self.state = "select_skill"
                                self.selected_skill = self.skills_library[0]
                            else:
                                print("No skills available, cannot start game")
                        else:
                            return False
        elif self.state == "select_skill":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if not self.skills_library:
                        if event.key == pygame.K_ESCAPE:
                            self.state = "menu"
                            self.selected_skill = None
                        continue
                    current_idx = self.skills_library.index(self.selected_skill) if self.selected_skill in self.skills_library else 0
                    if event.key == pygame.K_UP:
                        current_idx = (current_idx - 1) % len(self.skills_library)
                        self.selected_skill = self.skills_library[current_idx]
                    elif event.key == pygame.K_DOWN:
                        current_idx = (current_idx + 1) % len(self.skills_library)
                        self.selected_skill = self.skills_library[current_idx]
                    elif event.key == pygame.K_RETURN:
                        if self.selected_skill:
                            self.player = Player(pos=(0, 0), game=self)
                            if self.selected_skill.cooldown == 0:
                                self.selected_skill.use(self.player, self, self.current_time)
                            self.state = "select_weapons"
                        else:
                            print("No skill selected")
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                        self.selected_skill = None
                        self.player = None
        elif self.state == "select_weapons":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    max_weapons = self.player.max_weapons if self.player else MAX_WEAPONS_DEFAULT
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
                            self.start_game()
                        else:
                            print("At least one weapon must be selected")
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "select_skill"
                        self.selected_weapons.clear()
        elif self.state == "playing":
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
            current_room = self.dungeon.get_room(self.current_room_id)
            if dx != 0 or dy != 0:
                length = math.sqrt(dx**2 + dy**2)
                if length > 0:
                    dx /= length
                    dy /= length
                    self.player.move(dx, dy, dt, current_room)
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        idx = event.key - pygame.K_1
                        if idx < len(self.player.weapons):
                            self.player.current_weapon_idx = idx
                    if event.key == pygame.K_e and self.player.skill:
                        self.player.skill.use(self.player, self, self.current_time)
                    if event.key == pygame.K_c:
                        # self.dungeon_clear_count += 1
                        if self.dungeon_clear_count >= self.dungeon_clear_goal:
                            self.state = "win"
                        else:
                            print(f"已通過 {self.dungeon_clear_count} 次地牢，進入下一層！")
                            self._start_new_dungeon()
                            self._generate_new_enemies()
            mouse_pos = pygame.mouse.get_pos()
            direction = (mouse_pos[0] - (self.player.pos[0] + self.camera_offset[0]),
                         mouse_pos[1] - (self.player.pos[1] + self.camera_offset[1]))
            length = math.sqrt(direction[0]**2 + direction[1]**2)
            if length > 0:
                direction = (direction[0] / length, direction[1] / length)
            if pygame.mouse.get_pressed()[0]:
                bullet = self.player.fire(direction, self.current_time)
                if bullet:
                    self.player_bullet_group.add(bullet)
            # Update player bullets
            for bullet in self.player_bullet_group.copy():
                if not bullet.update(dt):
                    self.player_bullet_group.remove(bullet)
                else:
                    # Check for collisions with enemies
                    for enemy in self.enemy_group:
                        if bullet.rect.colliderect(enemy.rect):
                            enemy.take_damage(bullet.damage)
                            self.player_bullet_group.remove(bullet)
                            break  # Bullet can only hit one enemy
            # Update enemy bullets
            for bullet in self.enemy_bullet_group.copy():
                if not bullet.update(dt):
                    self.enemy_bullet_group.remove(bullet)
                elif bullet.shooter != self.player and self.player and self.player.invulnerable <= 0 and bullet.rect.colliderect(self.player.rect):
                    self.player.health -= bullet.damage
                    self.enemy_bullet_group.remove(bullet)
                    if self.player.health <= 0:
                        print("Player died!")  # Future: Implement game over state
            target_offset_x = -(self.player.pos[0] - SCREEN_WIDTH // 2)
            target_offset_y = -(self.player.pos[1] - SCREEN_HEIGHT // 2)
            self.camera_offset[0] += (target_offset_x - self.camera_offset[0]) * self.camera_lerp_factor * dt
            self.camera_offset[1] += (target_offset_y - self.camera_offset[1]) * self.camera_lerp_factor * dt
            if self.player:
                tile_x = int(self.player.pos[0] / TILE_SIZE)
                tile_y = int(self.player.pos[1] / TILE_SIZE)
                self.update_fog_map(tile_x, tile_y)
                current_pos = (self.player.pos[0], self.player.pos[1])
                if self.last_player_pos != current_pos or self.last_vision_radius != self.vision_radius:
                    self.update_fog_surface()
                    self.last_player_pos = current_pos
                    self.last_vision_radius = self.vision_radius
            if self.enemy_group:
                for enemy in self.enemy_group:
                    if enemy.health <= 0:
                        self.enemy_group.remove(enemy)
                    else:
                        enemy.update(dt, self.current_time)
            if self.dungeon.get_tile_at(self.player.pos) == 'End_room_portal':
                self.dungeon_clear_count += 1
                if self.dungeon_clear_count >= self.dungeon_clear_goal:
                    self.state = "win"
                else:
                    print(f"已通過 {self.dungeon_clear_count} 次地牢，進入下一層！")
                    self._start_new_dungeon()
                    self._generate_new_enemies()
        return True

    def update_fog_surface(self):
        self.fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.fog_surface.fill((0,0, 0, 255))
        center_x = self.player.rect.centerx + self.camera_offset[0]
        center_y = self.player.rect.centery + self.camera_offset[1]
        radius = int(self.vision_radius * TILE_SIZE)
        layers = 100
        max_alpha = 255
        for i in range(layers, 0, -1):
            alpha = int((i / layers) * max_alpha)
            current_radius = int((i / layers) * radius)
            pygame.draw.circle(
                self.fog_surface,
                (0, 0, 0, alpha),
                (center_x, center_y),
                current_radius
            )

    def draw_enemy(self, enemy):
        if enemy.health <= 0:
            return
        enemy_x = enemy.rect.x + self.camera_offset[0]
        enemy_y = enemy.rect.y + self.camera_offset[1]
        self.screen.blit(enemy.image, (enemy_x, enemy_y))
    
    def draw(self):
        self.screen.fill((0, 0, 0))
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "select_skill":
            self.draw_skill_selection()
        elif self.state == "select_weapons":
            self.draw_weapon_selection()
        elif self.state == "playing":
            # Draw 2.5D background
            view_left = max(0, int(-self.camera_offset[0] // TILE_SIZE - 1))
            view_right = min(self.dungeon.grid_width, int((-self.camera_offset[0] + SCREEN_WIDTH) // TILE_SIZE + 1))
            view_top = max(0, int(-self.camera_offset[1] // TILE_SIZE - 1))
            view_bottom = min(self.dungeon.grid_height, int((-self.camera_offset[1] + SCREEN_HEIGHT) // TILE_SIZE + 1))
            # Draw map tiles with 2.5D effect
            for row in range(view_top, view_bottom):
                for col in range(view_left, view_right):
                    x = col * TILE_SIZE + self.camera_offset[0]
                    y = row * TILE_SIZE + self.camera_offset[1]
                    try:
                        tile = self.dungeon.dungeon_tiles[row][col]
                        self.draw_3d_walls(row, col, x, y, tile)
                    except:
                        continue
            # Draw player
            self.screen.blit(self.player.image, (self.player.rect.x + self.camera_offset[0], self.player.rect.y + self.camera_offset[1]))
            for enemy in self.enemy_group:
                if enemy.health > 0 and enemy.pos[0] + self.camera_offset[0] >= 0 and enemy.pos[1] + self.camera_offset[1] >= 0:
                    self.draw_enemy(enemy)
            for row in range(view_top, view_bottom):
                for col in range(view_left, view_right):
                    x = col * TILE_SIZE + self.camera_offset[0]
                    y = row * TILE_SIZE + self.camera_offset[1]
                    try:
                        tile = self.dungeon.dungeon_tiles[row][col]
                        if tile == 'Border_wall':
                            # Draw 3D walls
                            self.draw_3d_walls(row, col, x, y, tile, True)
                    except:
                        continue
            # Draw player bullets
            for bullet in self.player_bullet_group:
                self.screen.blit(bullet.image, (bullet.rect.x + self.camera_offset[0], bullet.rect.y + self.camera_offset[1]))
            # Draw enemy bullets
            for bullet in self.enemy_bullet_group:
                self.screen.blit(bullet.image, (bullet.rect.x + self.camera_offset[0], bullet.rect.y + self.camera_offset[1]))
            # Apply fog of war
            if self.fog_surface:
                self.screen.blit(self.fog_surface, (0, 0))
            # Draw UI
            font = pygame.font.SysFont(None, 36)
            health_text = font.render(f"Health: {self.player.health}", True, (255, 255, 255))
            self.screen.blit(health_text, (10, 10))
            if self.player.weapons:
                weapon = self.player.weapons[self.player.current_weapon_idx]
                ammo_text = font.render(f"{weapon.name}: {weapon.ammo if not weapon.is_melee else '∞'}", True, (255, 255, 255))
                self.screen.blit(ammo_text, (10, 50))
            if self.player.skill:
                skill_text = font.render(f"Skill: {self.player.skill.name}", True, (255, 255, 255))
                self.screen.blit(skill_text, (10, 90))
                if self.player.skill.cooldown > 0:
                    cooldown = max(0, self.player.skill.cooldown - (self.current_time - self.player.skill.last_used))
                    cooldown_text = font.render(f"CD: {cooldown:.1f}s", True, (255, 255, 255))
                    self.screen.blit(cooldown_text, (10, 130))
            progress_text = font.render(f"Dungeon: {self.dungeon_clear_count+1}/{self.dungeon_clear_goal}", True, (255, 255, 0))
            self.screen.blit(progress_text, (10, 170))
            self.draw_minimap()
        elif self.state == "win":
            self.draw_win()
        pygame.display.flip()

    def draw_win(self):
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 48)
        win_text = font.render("Victory! You cleared all dungeons!", True, (255, 255, 0))
        self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - win_text.get_height() // 2))
        pygame.display.flip()