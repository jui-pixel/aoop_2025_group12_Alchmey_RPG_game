import pygame
from typing import List, Dict
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SKILLS_DEFAULT
from src.entities.skill.abstract_skill import Skill
import math

class EventManager:
    def __init__(self, game: 'Game'):
        """Initialize event manager to handle game input events.

        Args:
            game: The main game instance for interaction with other modules.
        """
        self.game = game  # Save game instance reference
        self.state = "menu"  # Initial game state is menu
        self.selected_menu_option = 0  # Current selected menu option index
        self.menu_options = ["Enter Lobby", "Exit"]  # Main menu options
        self.npc_menu_options = ["Select Skills", "Start Game"]  # NPC interaction menu options
        self.selected_npc_menu_option = 0  # Current selected NPC menu option index
        self.selected_skill = 0  # Current selected skill index
        self.selected_skills = []  # List of selected skills
        self.selected_skill_chain_idx = 0  # Current skill chain index

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events based on current game state.

        Args:
            event: Pygame event object.

        Dispatch event handling based on current game state (menu, skill_selection, lobby, playing).
        """
        if self.game.menu_manager.current_menu:
            print(f"EventManager: Passing event {event.type} to MenuManager due to active menu")
            self._handle_menu_event(event)
        elif self.state == "menu":
            self._handle_menu_event(event)
        elif self.state == "skill_selection":
            self._handle_skill_selection_event(event)
        elif self.state == "lobby":
            self._handle_lobby_event(event)
        elif self.state == "playing":
            self._handle_playing_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        """Handle events in menu state.

        Args:
            event: Pygame event object.

        Pass event to menu manager and perform actions based on returned action.
        """
        action = self.game.menu_manager.handle_event(event)
        if action:
            print(f"EventManager: Received action {action} from menu")
            if action == "enter_lobby":
                self.game.start_game()  # Enter lobby
                self.state = "lobby"
                print("EventManager: Entered lobby")
            elif action == "show_setting":
                print("EventManager: Showing settings menu (not implemented)")
                # TODO: Implement settings menu logic
            elif action == "exit":
                pygame.event.post(pygame.event.Event(pygame.QUIT))  # Exit game
                print("EventManager: Exiting game")
            elif action == "back_to_lobby":
                self.state = "lobby"
                self.game.hide_menu(self.game.menu_manager.current_menu.__class__.__name__.lower())
                print("EventManager: Returned to lobby")
            elif action == "close":
                self.game.hide_menu(self.game.menu_manager.current_menu.__class__.__name__.lower())
                print("EventManager: Closed menu")
            elif action.startswith("edit_chain_"):
                # No need to handle here as show_menu is called in the menu's handle_event
                pass

    def _handle_skill_selection_event(self, event: pygame.event.Event) -> None:
        """Handle events in skill selection state.

        Args:
            event: Pygame event object.

        Allow player to select skills using keyboard and add to skill chain.
        """
        max_skills = self.game.entity_manager.player.max_skills if self.game.entity_manager.player else MAX_SKILLS_DEFAULT
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_skill = (self.selected_skill - 1) % len(self.game.storage_manager.skills_library)  # Select previous skill
            elif event.key == pygame.K_DOWN:
                self.selected_skill = (self.selected_skill + 1) % len(self.game.storage_manager.skills_library)  # Select next skill
            elif event.key == pygame.K_RETURN:
                if len(self.selected_skills) < max_skills:
                    skill_dict = self.game.storage_manager.skills_library[self.selected_skill]
                    skill = self.game.storage_manager.get_skill_instance(skill_dict['name'])
                    if skill:
                        self.selected_skills.append(skill)
                        print(f"EventManager: Selected skill {skill.name}")
                if len(self.selected_skills) >= max_skills:
                    self.game.entity_manager.player.skill_chain[self.selected_skill_chain_idx] = self.selected_skills[:]  # Save skill chain
                    self.game.storage_manager.apply_skills_to_player()  # Apply skills to player
                    self.selected_skills = []  # Clear selected skills
                    self.state = "lobby"  # Return to lobby state
                    print("EventManager: Skill selection complete, returned to lobby")
            elif event.key == pygame.K_ESCAPE:
                self.state = "lobby"  # Cancel selection, return to lobby
                print("EventManager: Exited skill selection, returned to lobby")

    def _handle_lobby_event(self, event: pygame.event.Event) -> None:
        """Handle events in lobby state.

        Args:
            event: Pygame event object.

        Handle player movement (WASD keys) and NPC interaction or skill chain menu (E key).
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                interacted = self._handle_interaction()  # Handle NPC interaction
                if not interacted:
                    self.game.show_menu('skill_chain_menu')  # Open skill chain menu if no NPC
            elif event.key == pygame.K_w:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], -1)  # Move up
                print(f"EventManager: Lobby - Set displacement to {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_s:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], 1)  # Move down
                print(f"EventManager: Lobby - Set displacement to {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_a:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (-1, current_disp[1])  # Move left
                print(f"EventManager: Lobby - Set displacement to {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_d:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (1, current_disp[1])  # Move right
                print(f"EventManager: Lobby - Set displacement to {self.game.entity_manager.player.displacement}")
        elif event.type == pygame.KEYUP:
            current_disp = self.game.entity_manager.player.displacement
            if event.key in (pygame.K_w, pygame.K_s):
                self.game.entity_manager.player.displacement = (current_disp[0], 0)  # Reset vertical displacement
                print(f"EventManager: Lobby - Reset vertical displacement to {self.game.entity_manager.player.displacement}")
            elif event.key in (pygame.K_a, pygame.K_d):
                self.game.entity_manager.player.displacement = (0, current_disp[1])  # Reset horizontal displacement
                print(f"EventManager: Lobby - Reset horizontal displacement to {self.game.entity_manager.player.displacement}")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                mouse_pos = pygame.mouse.get_pos()  # Get mouse position
                target_pos = (mouse_pos[0] + self.game.render_manager.camera_offset[0], 
                              mouse_pos[1] + self.game.render_manager.camera_offset[1])  # Calculate target position
                dx = target_pos[0] - (self.game.entity_manager.player.x + self.game.entity_manager.player.w / 2)
                dy = target_pos[1] - (self.game.entity_manager.player.y + self.game.entity_manager.player.h / 2)
                magnitude = math.sqrt(dx**2 + dy**2)  # Calculate distance
                direction = (dx / magnitude, dy / magnitude) if magnitude > 0 else (0, 0)  # Calculate direction vector
                self.game.entity_manager.player.activate_skill(direction, self.game.current_time, target_pos)  # Activate skill
                self.game.audio_manager.play_sound_effect("skill_activate")  # Play skill sound effect
                print("EventManager: Playing - Activated skill")
            elif event.button == 2:
                pass
            elif event.button == 3:
                pass
            elif event.button == 4:  # Mouse wheel up: switch to next skill chain
                current_idx = self.game.entity_manager.player.current_skill_chain_idx
                next_idx = (current_idx + 1) % self.game.entity_manager.player.max_skill_chains
                self.game.entity_manager.player.switch_skill_chain(next_idx)
                print(f"EventManager: Playing - Switched to next skill chain {next_idx}")
            elif event.button == 5:  # Mouse wheel down: switch to previous skill chain
                current_idx = self.game.entity_manager.player.current_skill_chain_idx
                prev_idx = (current_idx - 1) % self.game.entity_manager.player.max_skill_chains
                self.game.entity_manager.player.switch_skill_chain(prev_idx)
                print(f"EventManager: Playing - Switched to previous skill chain {prev_idx}")
                
    def _handle_playing_event(self, event: pygame.event.Event) -> None:
        """Handle events in playing state.

        Args:
            event: Pygame event object.

        Handle player movement, skill switching (1-9 keys and mouse wheel), skill activation, and skill chain menu (E key if no NPC).
        """
        # if self.game.menu_manager.current_menu:
        #     print(f"EventManager: Skipping event {event.type} due to active menu {self.game.menu_manager.current_menu.__class__.__name__}")
        #     return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                interacted = self._handle_interaction()  # Handle NPC interaction
                if not interacted:
                    self.game.show_menu('skill_chain_menu')  # Open skill chain menu if no NPC
            elif event.key in range(pygame.K_1, pygame.K_9 + 1):
                chain_idx = event.key - pygame.K_1  # 1-9 keys map to chain_idx 0-8
                self.game.entity_manager.player.switch_skill_chain(chain_idx)
                print(f"EventManager: Playing - Switched skill chain to {chain_idx}")          
            elif event.key == pygame.K_w:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], -1)  # Move up
                print(f"EventManager: Playing - Set displacement to {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_s:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], 1)  # Move down
                print(f"EventManager: Playing - Set displacement to {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_a:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (-1, current_disp[1])  # Move left
                print(f"EventManager: Playing - Set displacement to {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_d:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (1, current_disp[1])  # Move right
                print(f"EventManager: Playing - Set displacement to {self.game.entity_manager.player.displacement}")
        elif event.type == pygame.KEYUP:
            current_disp = self.game.entity_manager.player.displacement
            if event.key in (pygame.K_w, pygame.K_s):
                self.game.entity_manager.player.displacement = (current_disp[0], 0)  # Reset vertical displacement
                print(f"EventManager: Playing - Reset vertical displacement to {self.game.entity_manager.player.displacement}")
            elif event.key in (pygame.K_a, pygame.K_d):
                self.game.entity_manager.player.displacement = (0, current_disp[1])  # Reset horizontal displacement
                print(f"EventManager: Playing - Reset horizontal displacement to {self.game.entity_manager.player.displacement}")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                mouse_pos = pygame.mouse.get_pos()  # Get mouse position
                target_pos = (mouse_pos[0] + self.game.render_manager.camera_offset[0], 
                              mouse_pos[1] + self.game.render_manager.camera_offset[1])  # Calculate target position
                dx = target_pos[0] - (self.game.entity_manager.player.x + self.game.entity_manager.player.w / 2)
                dy = target_pos[1] - (self.game.entity_manager.player.y + self.game.entity_manager.player.h / 2)
                magnitude = math.sqrt(dx**2 + dy**2)  # Calculate distance
                direction = (dx / magnitude, dy / magnitude) if magnitude > 0 else (0, 0)  # Calculate direction vector
                self.game.entity_manager.player.activate_skill(direction, self.game.current_time, target_pos)  # Activate skill
                self.game.audio_manager.play_sound_effect("skill_activate")  # Play skill sound effect
                print("EventManager: Playing - Activated skill")
            elif event.button == 2:
                pass
            elif event.button == 3:
                pass
            elif event.button == 4:  # Mouse wheel up: switch to next skill chain
                current_idx = self.game.entity_manager.player.current_skill_chain_idx
                next_idx = (current_idx + 1) % self.game.entity_manager.player.max_skill_chains
                self.game.entity_manager.player.switch_skill_chain(next_idx)
                print(f"EventManager: Playing - Switched to next skill chain {next_idx}")
            elif event.button == 5:  # Mouse wheel down: switch to previous skill chain
                current_idx = self.game.entity_manager.player.current_skill_chain_idx
                prev_idx = (current_idx - 1) % self.game.entity_manager.player.max_skill_chains
                self.game.entity_manager.player.switch_skill_chain(prev_idx)
                print(f"EventManager: Playing - Switched to previous skill chain {prev_idx}")

    def _handle_interaction(self) -> bool:
        """Handle interaction with the nearest NPC.

        Find the nearest NPC within interaction range and trigger interaction.

        Returns:
            bool: True if interacted with an NPC, False otherwise.
        """
        if not self.game.entity_manager.player:
            return False
        player = self.game.entity_manager.player
        nearest_npc = None
        min_distance = float('inf')
        for npc in self.game.entity_manager.entity_group:
            if hasattr(npc, 'interaction_range'):
                distance = npc.calculate_distance_to(player)  # Calculate distance to player
                if distance <= npc.interaction_range and distance < min_distance:
                    min_distance = distance
                    nearest_npc = npc
        if nearest_npc:
            nearest_npc.start_interaction()  # Trigger NPC interaction
            print(f"EventManager: Interacting with {nearest_npc.tag}")
            return True
        return False