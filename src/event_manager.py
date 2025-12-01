# src/event_manager.py
import pygame
from typing import List, Dict
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SKILLS_DEFAULT
from src.skills.abstract_skill import Skill
import math

# --- 為了 ECS 查詢兼容性，假設需要導入 ECS 組件 (例如 Position, Interactable) ---
# 實際部署時，請確保這些組件已正確導入
# from src.ecs.components import Position
# from src.ecs.components import Interactable
# ----------------------------------------------------------------------------------------


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
        self.selected_npc_menu_option = 0  # Current selected NPC menu index
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
                if self.game.menu_manager.current_menu:
                    self.game.hide_menu(self.game.menu_manager.current_menu.__class__.__name__.lower())
                print("EventManager: Returned to lobby")
            elif action == "close":
                if self.game.menu_manager.current_menu:
                    self.game.hide_menu(self.game.menu_manager.current_menu.__class__.__name__.lower())
                print("EventManager: Closed menu")
            elif action.startswith("edit_chain_"):
                # 【修正點 1】: 處理編輯技能鏈的動作，切換到技能選擇狀態
                try:
                    chain_idx = int(action.split('_')[-1])
                    player = self.game.entity_manager.player
                    if player and 0 <= chain_idx < player.max_skill_chains:
                        self.selected_skill_chain_idx = chain_idx # 設置要編輯的技能鏈索引
                        # 載入當前技能鏈中的技能列表，以便在選擇畫面中繼續編輯
                        self.selected_skills = player.skill_chain[chain_idx][:] 
                        self.state = "skill_selection" # 切換到技能選擇狀態
                        self.game.hide_menu('skill_chain_menu') # 隱藏技能鏈選單
                        print(f"EventManager: Entering skill selection for chain index {chain_idx}")
                    else:
                        print(f"EventManager: Invalid skill chain index: {chain_idx} or player not available.")
                except (ValueError, IndexError, AttributeError) as e:
                    print(f"EventManager: Failed to process action '{action}'. Error: {e}")

    def _handle_skill_selection_event(self, event: pygame.event.Event) -> None:
        """Handle events in skill selection state.

        Args:
            event: Pygame event object.

        Allow player to select skills using keyboard and add to skill chain.
        """
        # --- 修正: 使用更符合 ECS/Facade 命名慣例的屬性 ---
        # 假設 Player 門面已實現 max_skill_chain_length 屬性
        player = self.game.entity_manager.player
        max_skills = player.max_skill_chain_length if player else MAX_SKILLS_DEFAULT
        # --------------------------------------------------
        
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
                
                # 如果達到上限或手動按 Enter 結束
                if len(self.selected_skills) >= max_skills:
                    # skill_chain 屬性應返回對 PlayerComponent.skill_chain 的引用
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
        # 注意: 這裡的 player.displacement 屬性必須在 Player 門面中正確實現，
        # 才能讀取並設定 Velocity 組件中的移動方向。
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
        #    print(f"EventManager: Skipping event {event.type} due to active menu {self.game.menu_manager.current_menu.__class__.__name__}")
        #    return
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

        Find the nearest NPC within interaction range (ECS Query) and trigger interaction.

        Returns:
            bool: True if interacted with an NPC, False otherwise.
        """
        if not self.game.entity_manager.player:
            return False
        
        player = self.game.entity_manager.player
        world = self.game.entity_manager.world
        
        # 假設 Player Facade (player) 提供 x, y, w, h 屬性來獲取實體中心點
        player_center_x = player.x + player.w / 2
        player_center_y = player.y + player.h / 2

        nearest_npc_id = None
        min_distance = float('inf')
        nearest_npc_tag = None
        nearest_npc_comp = None # Used to store the Interactable component

        # --- ECS 兼容性修正: 使用 world.get_components 查詢 NPC ---
        
        # 假設 EntityManager 有一個方法來獲取所有可互動實體及其組件
        if hasattr(self.game.entity_manager, 'get_interactable_entities'):
            # 假設此方法返回 (entity_id, position_comp, interactable_comp) 的迭代器
            for entity_id, pos_comp, interactable_comp in self.game.entity_manager.get_interactable_entities():
                # 排除玩家自己 (假設 Facade/EntityFactory 會確保 NPC 不會是玩家ID)
                if entity_id == player.ecs_entity:
                    continue
                    
                # 獲取 NPC 中心點座標
                npc_center_x = pos_comp.x + interactable_comp.w / 2 if hasattr(interactable_comp, 'w') else pos_comp.x
                npc_center_y = pos_comp.y + interactable_comp.h / 2 if hasattr(interactable_comp, 'h') else pos_comp.y
                
                dx = player_center_x - npc_center_x
                dy = player_center_y - npc_center_y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance <= interactable_comp.interaction_range and distance < min_distance:
                    min_distance = distance
                    nearest_npc_id = entity_id
                    nearest_npc_tag = interactable_comp.tag
                    nearest_npc_comp = interactable_comp

            if nearest_npc_id:
                # 觸發互動，假設 Interactable 組件包含 start_interaction() 方法
                nearest_npc_comp.start_interaction() 
                print(f"EventManager: Interacting with {nearest_npc_tag}")
                return True
        else:
            # 如果沒有抽象化的方法，我們無法安全地進行 ECS 查詢，
            # 因此我們將輸出錯誤訊息，並保持不互動
            print("EventManager: ECS query helper not found. Cannot perform interaction check.")
            return False
        # 【修正點 2】: 移除這裡冗餘的菜單開啟邏輯。
        # self.game.show_menu('skill_chain_menu') 
        return False