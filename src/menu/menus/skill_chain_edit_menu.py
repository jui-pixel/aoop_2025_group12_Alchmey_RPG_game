# src/menu/menus/skill_chain_edit_menu.py
from src.menu.abstract_menu import AbstractMenu
from src.menu.button import Button
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from math import ceil
from typing import List, Optional
from src.skills.skill import create_skill_from_dict

class SkillChainEditMenu(AbstractMenu):
    def __init__(self, game: 'Game', chain_idx: int, options=None):
        """Initialize the skill chain edit menu for a specific chain."""
        self.title = f"Edit Skill Chain {chain_idx + 1}"
        self.game = game
        self.chain_idx = chain_idx
        self.options = options
        self.slots: List[Optional['Skill']] = self.game.entity_manager.player.skill_chain[chain_idx][:]
        self.slots += [None] * (8 - len(self.slots))  # Pad to 8 slots
        self.marked_slot: Optional[int] = None
        self.current_page = 0
        self.skills = self.game.storage_manager.skills_library
        self.skills_per_page = 8
        self.total_pages = ceil(len(self.skills) / self.skills_per_page) if self.skills else 1
        self.buttons = []
        self.selected_index = 0  # Initialize selected_index
        self.active = False
        self.font = pygame.font.SysFont(None, 48)
        self.skill_font = pygame.font.SysFont(None, 36)
        self._update_buttons()

    def _update_buttons(self):
        """Update the button list for slots, skills, and navigation."""
        self.buttons = []
        # Slot buttons: left 4 (1-4 vertical), middle-left 4 (5-8 vertical)
        for i in range(8):
            col = i // 4  # 0 for left, 1 for middle-left
            row = i % 4
            slot_text = self.slots[i].name if self.slots[i] else "Empty"
            action = f"mark_slot_{i}"
            self.buttons.append(
                Button(
                    100 + col * 200, 100 + row * 50, 180, 40,
                    slot_text, pygame.Surface((180, 40)), action,
                    self.skill_font
                )
            )
        # Skill library buttons on the right
        start_idx = self.current_page * self.skills_per_page
        end_idx = min(start_idx + self.skills_per_page, len(self.skills))
        for i, idx in enumerate(range(start_idx, end_idx)):
            skill_dict = self.skills[idx]
            button_text = skill_dict['name']
            action = f"assign_skill_{idx}"
            self.buttons.append(
                Button(
                    SCREEN_WIDTH - 300, 100 + i * 50, 280, 40,
                    button_text, pygame.Surface((280, 40)), action,
                    self.skill_font
                )
            )
        # Navigation buttons for skill library
        y_offset = 100 + self.skills_per_page * 50
        if self.current_page > 0:
            self.buttons.append(
                Button(
                    SCREEN_WIDTH - 300, y_offset, 140, 40,
                    "Previous", pygame.Surface((140, 40)), "previous",
                    self.skill_font
                )
            )
        if self.current_page < self.total_pages - 1:
            self.buttons.append(
                Button(
                    SCREEN_WIDTH - 150, y_offset, 140, 40,
                    "Next", pygame.Surface((140, 40)), "next",
                    self.skill_font
                )
            )
        # Complete button at bottom right
        self.buttons.append(
            Button(
                SCREEN_WIDTH - 200, SCREEN_HEIGHT - 100, 150, 40,
                "Complete", pygame.Surface((150, 40)), "skill_chain_menu",
                self.skill_font
            )
        )

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the skill chain edit menu, including slots, skill library, and marked slot highlight."""
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))
        for button in self.buttons:
            button.draw(screen)
        # Highlight marked slot with gold border
        if self.marked_slot is not None:
            slot_button = next(b for b in self.buttons if b.action == f"mark_slot_{self.marked_slot}")
            pygame.draw.rect(screen, (255, 215, 0), slot_button.rect, 3)  # Gold border

    def handle_event(self, event: pygame.event.Event) -> str:
        """Handle events for marking slots, assigning skills, clearing with middle click, and navigation."""
        if not self.active:
            return ""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._save_chain()
            self.game.hide_menu('skill_chain_edit_menu')
            return "close"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button to clear slot
                for button in self.buttons:
                    if button.rect.collidepoint(event.pos) and button.action.startswith("mark_slot_"):
                        slot_idx = int(button.action.split("_")[2])
                        self.slots[slot_idx] = None
                        button.text = "Empty"
                        print(f"Cleared slot {slot_idx}")
                        return "clear_slot"
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.buttons[self.selected_index].is_selected = False
                    self.selected_index = i
                    self.buttons[self.selected_index].is_selected = True
                    break
        for button in self.buttons:
            active, action = button.handle_event(event)
            if active:
                if action.startswith("mark_slot_"):
                    self.marked_slot = int(action.split("_")[2])
                    return "mark_slot"
                elif action.startswith("assign_skill_"):
                    skill_idx = int(action.split("_")[2])
                    if self.marked_slot is not None:
                        skill_dict = self.skills[skill_idx]
                        self.slots[self.marked_slot] = create_skill_from_dict(skill_dict)
                        slot_button = next(b for b in self.buttons if b.action == f"mark_slot_{self.marked_slot}")
                        slot_button.text = self.slots[self.marked_slot].name
                        self.marked_slot = None
                        return "assign_skill"
                elif action == "previous" and self.current_page > 0:
                    self.current_page -= 1
                    self.selected_index = 0
                    self._update_buttons()
                    return "previous"
                elif action == "next" and self.current_page < self.total_pages - 1:
                    self.current_page += 1
                    self.selected_index = 0
                    self._update_buttons()
                    return "next"
                elif action == "skill_chain_menu":
                    self._save_chain()
                    self.game.hide_menu(self.__class__.__name__)
                    self.game.show_menu('skill_chain_menu')
                    return "skill_chain_menu"
        return ""

    def _save_chain(self):
        """Save the edited chain by removing empty slots and updating the player's skill chain."""
        self.slots = [s for s in self.slots if s is not None]
        if not self.slots:
            self.slots = []  # Keep empty if all were None
        self.game.entity_manager.player.skill_chain[self.chain_idx] = self.slots
        self.game.entity_manager.player.current_skill_idx = 0
        print(f"Saved skill chain {self.chain_idx + 1}: {[s.name if s else 'None' for s in self.slots]}")

    def get_selected_action(self) -> str:
        return self.buttons[self.selected_index].action if self.active else ""

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            self._update_buttons()
            self.buttons[self.selected_index].is_selected = True
        else:
            self.buttons[self.selected_index].is_selected = False
            self.marked_slot = None