import pygame
import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from src.weapons.weapon import *
from src.skills.skill import *
from src.dungeon.dungeon import *
from src.config import *
from src.character.character import *


class Game:
    def __init__(self, screen, pygame_clock):
        self.screen = screen
        self.clock = pygame_clock
        self.dungeon = Dungeon()
        self.dungeon.game = self
        self.player = None
        self.bullet_group = pygame.sprite.Group()
        self.current_time = 0.0
        self.state = "menu"
        self.selected_skill = None
        self.selected_weapons = []
        self.menu_options = ["Start Game", "Exit"]
        self.selected_menu_option = 0
        self.camera_lerp_factor = 1.5
        self.current_room_id = 0
        self.skills_library = [
            Skill("Restore Ammo", 30.0, lambda p: self.restore_ammo_effect(p)),
            Skill("Carry 10 Weapons", 0.0, lambda p: setattr(p, 'max_weapons', 10)),
            Skill("Shadow Dash", 15.0, lambda p: self.dash_invulnerable_effect(p)),
            Skill("Time Warp", 15.0, lambda p: self.time_slow_effect(p))
        ]
        self.weapons_library = [Gun(), Bow(), Staff(), Knife()]
        self.camera_offset = [0, 0]
        self.time_scale = 1.0

    def restore_ammo_effect(self, player: 'Player'):
        for weapon in player.weapons:
            if not weapon.is_melee:
                weapon.ammo = weapon.max_ammo

    def dash_invulnerable_effect(self, player: 'Player'):
        direction = (0, -1)
        player.pos = (player.pos[0] + direction[0] * 5 * TILE_SIZE,
                      player.pos[1] + direction[1] * 5 * TILE_SIZE)
        player.rect.center = player.pos
        player.invulnerable = 1.0

    def time_slow_effect(self, player: 'Player'):
        self.time_scale = 0.5
        pygame.time.set_timer(pygame.USEREVENT, 2000)

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
        title = font.render("Select a Skill", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 36))
        for i, skill in enumerate(self.skills_library):
            color = (255, 255, 0) if skill == self.selected_skill else (255, 255, 255)
            text = font.render(skill.name, True, color)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 100 + i * 40))
        pygame.display.flip()

    def draw_weapon_selection(self):
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
        title = font.render(f"Select Weapons (Max: {self.player.max_weapons if self.player else MAX_WEAPONS_DEFAULT})", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 36))
        for i, weapon in enumerate(self.weapons_library):
            count = self.selected_weapons.count(weapon)
            text = font.render(f"{weapon.name} (Selected: {count})", True, (255, 255, 255))
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 100 + i * 40))
        instruction = font.render("Press ENTER to start", True, (255, 255, 255))
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 400))
        pygame.display.flip()

    def draw_win(self):
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 72)
        text = font.render("You Win!", True, (255, 255, 255))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2))
        pygame.display.flip()

    def start_game(self):
        self.dungeon.initialize_dungeon()
        spawn_room = self.dungeon.get_room(0)
        center_tile_x = int(spawn_room.x + spawn_room.width // 2)
        center_tile_y = int(spawn_room.y + spawn_room.height // 2)
        center_x = center_tile_x * TILE_SIZE
        center_y = center_tile_y * TILE_SIZE
        self.player = Player(pos=(center_x, center_y), game=self)
        print(f"遊戲開始：玩家生成在 ({center_x}, {center_y})，房間 ID: 0")
        print(f"生成瓦片: ({center_tile_x}, {center_tile_y})，瓦片值: {self.dungeon.dungeon_tiles[center_tile_y][center_tile_x]}")
        self.player.skill = self.selected_skill
        if self.player.skill and self.player.skill.cooldown == 0:
            self.player.skill.use(self.player, self.current_time)
        self.player.weapons = self.selected_weapons
        self.state = "playing"
        self.camera_offset = [-(self.player.pos[0] - SCREEN_WIDTH // 2),
                              -(self.player.pos[1] - SCREEN_HEIGHT // 2)]

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
                    if event.key == pygame.K_DOWN:
                        self.selected_menu_option = (self.selected_menu_option + 1) % len(self.menu_options)
                    if event.key == pygame.K_RETURN:
                        if self.menu_options[self.selected_menu_option] == "Start Game":
                            self.state = "select_skill"
                            self.selected_skill = self.skills_library[0]
                        else:
                            return False
        elif self.state == "select_skill":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    current_idx = self.skills_library.index(self.selected_skill)
                    if event.key == pygame.K_UP:
                        current_idx = (current_idx - 1) % len(self.skills_library)
                    elif event.key == pygame.K_DOWN:
                        current_idx = (current_idx + 1) % len(self.skills_library)
                    elif event.key == pygame.K_RETURN:
                        self.player = Player(pos=(0, 0), game=self)
                        self.selected_skill = self.skills_library[current_idx]
                        if self.selected_skill.cooldown == 0:
                            self.selected_skill.use(self.player, self.current_time)
                        self.state = "select_weapons"
        elif self.state == "select_weapons":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        idx = event.key - pygame.K_1
                        if idx < len(self.weapons_library) and len(self.selected_weapons) < self.player.max_weapons:
                            self.selected_weapons.append(self.weapons_library[idx])
                    elif event.key == pygame.K_BACKSPACE and self.selected_weapons:
                        self.selected_weapons.pop()
                    elif event.key == pygame.K_RETURN and self.selected_weapons:
                        self.start_game()
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
                        self.player.skill.use(self.player, self.current_time)
            mouse_pos = pygame.mouse.get_pos()
            direction = (mouse_pos[0] - (self.player.pos[0] + self.camera_offset[0]),
                         mouse_pos[1] - (self.player.pos[1] + self.camera_offset[1]))
            length = math.sqrt(direction[0]**2 + direction[1]**2)
            if length > 0:
                direction = (direction[0] / length, direction[1] / length)
            if pygame.mouse.get_pressed()[0]:
                bullet = self.player.fire(direction, self.current_time)
                if bullet:
                    self.bullet_group.add(bullet)
            self.bullet_group.update(dt)
            for bullet in self.bullet_group.copy():
                if not bullet.update(dt):
                    self.bullet_group.remove(bullet)
            target_offset_x = -(self.player.pos[0] - SCREEN_WIDTH // 2)
            target_offset_y = -(self.player.pos[1] - SCREEN_HEIGHT // 2)
            self.camera_offset[0] += (target_offset_x - self.camera_offset[0]) * self.camera_lerp_factor * dt
            self.camera_offset[1] += (target_offset_y - self.camera_offset[1]) * self.camera_lerp_factor * dt
            # Check if player is on the goal tile
            if self.dungeon.get_tile_at(self.player.pos) == 'G':
                self.state = "win"
        return True

    def draw(self):
        self.screen.fill((0, 0, 0))
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "select_skill":
            self.draw_skill_selection()
        elif self.state == "select_weapons":
            self.draw_weapon_selection()
        elif self.state == "playing":
            view_left = max(0, int(-self.camera_offset[0] // TILE_SIZE - 1))
            view_right = min(self.dungeon.grid_width, int((-self.camera_offset[0] + SCREEN_WIDTH) // TILE_SIZE + 1))
            view_top = max(0, int(-self.camera_offset[1] // TILE_SIZE - 1))
            view_bottom = min(self.dungeon.grid_height, int((-self.camera_offset[1] + SCREEN_HEIGHT) // TILE_SIZE + 1))
            for row in range(view_top, view_bottom):
                for col in range(view_left, view_right):
                    x = col * TILE_SIZE + self.camera_offset[0]
                    y = row * TILE_SIZE + self.camera_offset[1]
                    try:
                        tile = self.dungeon.dungeon_tiles[row][col]
                        color = {
                            'F': ROOM_FLOOR_COLOR,
                            'Room_wall': ROOM_WALL_COLOR,
                            'E': END_ROOM_FLOOR_COLAR,  # Magenta for end room floor
                            'G': END_ROOM_PROTAL_COLOR   # Yellow for goal marker
                        }.get(tile, OUTSIDE_COLOR)
                        pygame.draw.rect(self.screen, color, (x, y, TILE_SIZE, TILE_SIZE))
                        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, TILE_SIZE, TILE_SIZE), 1)
                    except:
                        continue
            self.screen.blit(self.player.image, (self.player.rect.x + self.camera_offset[0], self.player.rect.y + self.camera_offset[1]))
            for bullet in self.bullet_group:
                self.screen.blit(bullet.image, (bullet.rect.x + self.camera_offset[0], bullet.rect.y + self.camera_offset[1]))
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
        elif self.state == "win":
            self.draw_win()
        pygame.display.flip()
