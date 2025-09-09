import pygame
from typing import List
from .config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SKILLS_DEFAULT, MAX_WEAPONS_DEFAULT

class RenderManager:
    def __init__(self, game: 'Game', screen: pygame.Surface):
        self.game = game
        self.screen = screen
        self.camera_offset = [0, 0]
        self.camera_lerp_factor = 1.5
        self.original_camera_lerp_factor = 1.5
        self.minimap_scale = 1
        self.skill_rects = []

    def update_camera(self, dt: float) -> None:
        """Update camera to follow the player."""
        if self.game.entity_manager.player:
            target_x = self.game.entity_manager.player.x - SCREEN_WIDTH // 2
            target_y = self.game.entity_manager.player.y - SCREEN_HEIGHT // 2
            self.camera_offset[0] += (target_x - self.camera_offset[0]) * self.camera_lerp_factor * dt
            self.camera_offset[1] += (target_y - self.camera_offset[1]) * self.camera_lerp_factor * dt

    def draw_game_world(self) -> None:
        """Draw the game world, including dungeon and entities."""
        self.screen.fill((0, 0, 0))
        dungeon = self.game.dungeon_manager.get_dungeon()
        dungeon.draw_background(self.screen, self.camera_offset)
        self.game.entity_manager.draw(self.screen, self.camera_offset)
        dungeon.draw_foreground(self.screen, self.camera_offset)

    def draw_menu(self) -> None:
        """Draw the main menu."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 48)
        for i, option in enumerate(self.game.event_manager.menu_options):
            color = (255, 255, 0) if i == self.game.event_manager.selected_menu_option else (255, 255, 255)
            text = font.render(option, True, color)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200 + i * 50))
        pygame.display.flip()

    def draw_skill_selection(self) -> None:
        """Draw the skill selection screen."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
        max_skills = self.game.entity_manager.player.max_skills if self.game.entity_manager.player else MAX_SKILLS_DEFAULT
        self.skill_rects = []

        if not self.game.storage_manager.skills_library:
            error_text = font.render("No skills available!", True, (255, 0, 0))
            self.screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 100))
        else:
            for i, skill in enumerate(self.game.storage_manager.skills_library):
                count = self.game.event_manager.selected_skills.count(skill)
                is_selected = skill in self.game.event_manager.selected_skills
                mouse_pos = pygame.mouse.get_pos()
                hovered = False
                for j, rect in enumerate(self.skill_rects):
                    if rect.collidepoint(mouse_pos) and i == j:
                        hovered = True
                        break
                color = (0, 255, 0) if is_selected else (255, 255, 0) if hovered else (255, 255, 255)
                text = font.render(f"{skill['name']} (Selected: {count}, Energy Cost: {skill['energy_cost']})", True, color)
                x = SCREEN_WIDTH // 2 - text.get_width() // 2
                y = 100 + i * 40
                self.screen.blit(text, (x, y))
                rect = pygame.Rect(x, y, text.get_width(), text.get_height())
                self.skill_rects.append(rect)
                if is_selected:
                    pygame.draw.rect(self.screen, (0, 255, 0), rect, 2)
                elif hovered:
                    pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)

        chain_text = font.render(f"Skill Chain {self.game.event_manager.selected_skill_chain_idx + 1}/{self.game.entity_manager.player.max_skill_chains}", True, (255, 255, 255))
        self.screen.blit(chain_text, (SCREEN_WIDTH // 2 - chain_text.get_width() // 2, 450))
        count_text = font.render(f"Selected: {len(self.game.event_manager.selected_skills)}/{max_skills}", True, (255, 255, 255))
        self.screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 400))
        pygame.display.flip()

    def draw_lobby(self) -> None:
        """Draw the lobby state."""
        self.draw_game_world()
        pygame.display.flip()

    def draw_playing(self) -> None:
        """Draw the playing state."""
        self.draw_game_world()
        if self.game.entity_manager.player and self.game.entity_manager.player.skill_chain[self.game.entity_manager.player.current_skill_chain_idx]:
            font = pygame.font.SysFont(None, 36)
            skill_name = self.game.entity_manager.player.skill_chain[self.game.entity_manager.player.current_skill_chain_idx][self.game.entity_manager.player.current_skill_idx].name
            skill_text = font.render(f"Current Skill: {skill_name}", True, (255, 255, 255))
            self.screen.blit(skill_text, (10, 50))
        pygame.display.flip()

    def draw_win(self) -> None:
        """Draw the victory screen."""
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 48)
        win_text = font.render("Victory! You cleared all dungeons!", True, (255, 255, 0))
        self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - win_text.get_height() // 2))
        pygame.display.flip()