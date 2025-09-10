import pygame
from typing import List, Dict
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SKILLS_DEFAULT
from src.entities.skill.skill import Skill
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
        # 僅通過 menu_manager 處理選單事件
        action = self.game.menu_manager.handle_event(event)
        if action:
            print(f"EventManager: Received action {action} from menu")
            if action == "enter_lobby":
                self.game.start_game()
                self.state = "lobby"
                print("EventManager: Entered lobby")
            elif action == "show_setting":
                print("EventManager: Show settings (not implemented)")
                # TODO: 實現設置選單
            elif action == "exit":
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                print("EventManager: Exit game")

    def _handle_skill_selection_event(self, event: pygame.event.Event) -> None:
        """Handle events in the skill selection state."""
        max_skills = self.game.entity_manager.player.max_skills if self.game.entity_manager.player else MAX_SKILLS_DEFAULT
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_skill = (self.selected_skill - 1) % len(self.game.storage_manager.skills)
            elif event.key == pygame.K_DOWN:
                self.selected_skill = (self.selected_skill + 1) % len(self.game.storage_manager.skills)
            elif event.key == pygame.K_RETURN:
                if len(self.selected_skills) < max_skills:
                    self.selected_skills.append(self.game.storage_manager.skills[self.selected_skill])
                if len(self.selected_skills) >= max_skills:
                    self.game.entity_manager.player.skill_chain[self.selected_skill_chain_idx] = self.selected_skills[:]
                    self.selected_skills = []
                    self.state = "lobby"
                    print("EventManager: Skill selection completed, returned to lobby")
            elif event.key == pygame.K_ESCAPE:
                self.state = "lobby"
                print("EventManager: Escaped skill selection, returned to lobby")

    def _handle_lobby_event(self, event: pygame.event.Event) -> None:
        """Handle events in the lobby state."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                self._handle_interaction()
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
            if event.key == pygame.K_q:
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

    def _handle_interaction(self) -> None:
        """Find nearest NPC within range and trigger interaction."""
        if not self.game.entity_manager.player:
            return
        player = self.game.entity_manager.player
        nearest_npc = None
        min_distance = float('inf')
        for npc in self.game.entity_manager.npc_group:
            if hasattr(npc, 'interaction_range'):
                distance = npc.calculate_distance_to(player)
                if distance <= npc.interaction_range and distance < min_distance:
                    min_distance = distance
                    nearest_npc = npc
        if nearest_npc:
            nearest_npc.start_interaction()
            print(f"EventManager: Interacting with {nearest_npc.tag}")