import pygame
from typing import List, Dict
from .config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SKILLS_DEFAULT
from .entities.skill.skill import Skill
import math

class EventManager:
    def __init__(self, game: 'Game'):
        self.game = game
        self.state = "menu"
        self.selected_menu_option = 0
        self.menu_options = ["Enter Lobby", "Exit"]
        self.npc_menu_options = ["Select Skills", "Start Game"]
        self.selected_npc_menu_option = 0
        self.selected_skill = 0
        self.selected_skills = []
        self.selected_skill_chain_idx = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events based on game state."""
        if self.state == "menu":
            self._handle_menu_event(event)
        elif self.state == "skill_selection":
            self._handle_skill_selection_event(event)
        elif self.state == "lobby":
            self._handle_lobby_event(event)
        elif self.state == "playing":
            self._handle_playing_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        """Handle events in the menu state."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_menu_option = (self.selected_menu_option - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.selected_menu_option = (self.selected_menu_option + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                if self.menu_options[self.selected_menu_option] == "Enter Lobby":
                    self.game.start_game()  # Initialize player and dungeon
                    self.state = "lobby"
                elif self.menu_options[self.selected_menu_option] == "Exit":
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _handle_skill_selection_event(self, event: pygame.event.Event) -> None:
        """Handle events in the skill selection state."""
        max_skills = self.game.entity_manager.player.max_skills if self.game.entity_manager.player else MAX_SKILLS_DEFAULT
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_skill = (self.selected_skill - 1) % len(self.game.storage_manager.skills_library)
            elif event.key == pygame.K_DOWN:
                self.selected_skill = (self.selected_skill + 1) % len(self.game.storage_manager.skills_library)
            elif event.key == pygame.K_LEFT:
                self.selected_skill_chain_idx = (self.selected_skill_chain_idx - 1) % self.game.entity_manager.player.max_skill_chains
            elif event.key == pygame.K_RIGHT:
                self.selected_skill_chain_idx = (self.selected_skill_chain_idx + 1) % self.game.entity_manager.player.max_skill_chains
            elif event.key == pygame.K_RETURN:
                if len(self.selected_skills) < max_skills:
                    self.selected_skills.append(self.game.storage_manager.skills_library[self.selected_skill])
            elif event.key == pygame.K_SPACE:
                if self.selected_skills:
                    for skill_data in self.selected_skills:
                        skill = Skill(**skill_data)
                        self.game.entity_manager.player.add_skill_to_chain(skill, self.selected_skill_chain_idx)
                    self.game.start_game()
            elif event.key == pygame.K_ESCAPE:
                self.state = "menu"

    def _handle_lobby_event(self, event: pygame.event.Event) -> None:
        """Handle events in the lobby state."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.state = "playing"
            elif event.key == pygame.K_w:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], -1)
            elif event.key == pygame.K_s:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], 1)
            elif event.key == pygame.K_a:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (-1, current_disp[1])
            elif event.key == pygame.K_d:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (1, current_disp[1])
        elif event.type == pygame.KEYUP:
            current_disp = self.game.entity_manager.player.displacement
            if event.key in (pygame.K_w, pygame.K_s):
                self.game.entity_manager.player.displacement = (current_disp[0], 0)
            elif event.key in (pygame.K_a, pygame.K_d):
                self.game.entity_manager.player.displacement = (0, current_disp[1])

    def _handle_playing_event(self, event: pygame.event.Event) -> None:
        """Handle events in the playing state."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                skill_index = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4].index(event.key)
                self.game.entity_manager.player.switch_skill(skill_index)
            elif event.key == pygame.K_q:
                self.game.entity_manager.player.switch_skill_chain((self.game.entity_manager.player.current_skill_chain_idx - 1) % self.game.entity_manager.player.max_skill_chains)
            elif event.key == pygame.K_e:
                self.game.entity_manager.player.switch_skill_chain((self.game.entity_manager.player.current_skill_chain_idx + 1) % self.game.entity_manager.player.max_skill_chains)
            elif event.key == pygame.K_SPACE:
                mouse_pos = pygame.mouse.get_pos()
                target_pos = (mouse_pos[0] + self.game.render_manager.camera_offset[0], 
                             mouse_pos[1] + self.game.render_manager.camera_offset[1])
                dx = target_pos[0] - self.game.entity_manager.player.x
                dy = target_pos[1] - self.game.entity_manager.player.y
                magnitude = math.sqrt(dx**2 + dy**2)
                direction = (dx / magnitude, dy / magnitude) if magnitude > 0 else (0, 0)
                self.game.entity_manager.player.activate_skill(direction, self.game.current_time, target_pos)
                self.game.audio_manager.play_sound_effect("skill_activate")
            elif event.key == pygame.K_w:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], -1)
            elif event.key == pygame.K_s:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], 1)
            elif event.key == pygame.K_a:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (-1, current_disp[1])
            elif event.key == pygame.K_d:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (1, current_disp[1])
        elif event.type == pygame.KEYUP:
            current_disp = self.game.entity_manager.player.displacement
            if event.key in (pygame.K_w, pygame.K_s):
                self.game.entity_manager.player.displacement = (current_disp[0], 0)
            elif event.key in (pygame.K_a, pygame.K_d):
                self.game.entity_manager.player.displacement = (0, current_disp[1])