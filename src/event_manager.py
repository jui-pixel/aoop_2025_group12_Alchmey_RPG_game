import pygame
from typing import List, Dict
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SKILLS_DEFAULT
from src.entities.skill.skill import Skill
import math

class EventManager:
    def __init__(self, game: 'Game'):
        """初始化事件管理器，負責處理遊戲中的輸入事件。

        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
        """
        self.game = game  # 保存遊戲實例引用
        self.state = "menu"  # 初始遊戲狀態為菜單
        self.selected_menu_option = 0  # 當前選中的菜單選項索引
        self.menu_options = ["Enter Lobby", "Exit"]  # 主菜單選項
        self.npc_menu_options = ["Select Skills", "Start Game"]  # NPC 交互菜單選項
        self.selected_npc_menu_option = 0  # 當前選中的 NPC 菜單選項索引
        self.selected_skill = 0  # 當前選中的技能索引
        self.selected_skills = []  # 已選擇的技能列表
        self.selected_skill_chain_idx = 0  # 當前技能鏈索引

    def handle_event(self, event: pygame.event.Event) -> None:
        """根據遊戲狀態處理輸入事件。

        Args:
            event: Pygame 事件對象。

        根據當前遊戲狀態（menu, skill_selection, lobby, playing）分派事件處理。
        """
        if self.game.menu_manager.current_menu:
            print(f"EventManager: 由於有活動菜單，將事件 {event.type} 傳遞給 MenuManager")
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
        """處理菜單狀態的事件。

        Args:
            event: Pygame 事件對象。

        將事件傳遞給菜單管理器，並根據返回的動作執行相應操作。
        """
        action = self.game.menu_manager.handle_event(event)
        if action:
            print(f"EventManager: 從菜單收到動作 {action}")
            if action == "enter_lobby":
                self.game.start_game()  # 進入大廳
                self.state = "lobby"
                print("EventManager: 已進入大廳")
            elif action == "show_setting":
                print("EventManager: 顯示設置菜單（尚未實現）")
                # TODO: 實現設置菜單邏輯
            elif action == "exit":
                pygame.event.post(pygame.event.Event(pygame.QUIT))  # 退出遊戲
                print("EventManager: 退出遊戲")

    def _handle_skill_selection_event(self, event: pygame.event.Event) -> None:
        """處理技能選擇狀態的事件。

        Args:
            event: Pygame 事件對象。

        允許玩家使用鍵盤選擇技能並添加到技能鏈。
        """
        max_skills = self.game.entity_manager.player.max_skills if self.game.entity_manager.player else MAX_SKILLS_DEFAULT
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_skill = (self.selected_skill - 1) % len(self.game.storage_manager.skills)  # 向上選擇技能
            elif event.key == pygame.K_DOWN:
                self.selected_skill = (self.selected_skill + 1) % len(self.game.storage_manager.skills)  # 向下選擇技能
            elif event.key == pygame.K_RETURN:
                if len(self.selected_skills) < max_skills:
                    self.selected_skills.append(self.game.storage_manager.skills[self.selected_skill])  # 添加選中的技能
                if len(self.selected_skills) >= max_skills:
                    self.game.entity_manager.player.skill_chain[self.selected_skill_chain_idx] = self.selected_skills[:]  # 保存技能鏈
                    self.selected_skills = []  # 清空已選擇技能
                    self.state = "lobby"  # 返回大廳狀態
                    print("EventManager: 技能選擇完成，返回大廳")
            elif event.key == pygame.K_ESCAPE:
                self.state = "lobby"  # 取消選擇，返回大廳
                print("EventManager: 退出技能選擇，返回大廳")

    def _handle_lobby_event(self, event: pygame.event.Event) -> None:
        """處理大廳狀態的事件。

        Args:
            event: Pygame 事件對象。

        處理玩家移動（WASD 鍵）和與 NPC 的交互（E 鍵）。
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                self._handle_interaction()  # 處理與 NPC 的交互
            elif event.key == pygame.K_w:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], -1)  # 向上移動
                print(f"EventManager: 大廳 - 設置位移為 {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_s:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], 1)  # 向下移動
                print(f"EventManager: 大廳 - 設置位移為 {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_a:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (-1, current_disp[1])  # 向左移動
                print(f"EventManager: 大廳 - 設置位移為 {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_d:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (1, current_disp[1])  # 向右移動
                print(f"EventManager: 大廳 - 設置位移為 {self.game.entity_manager.player.displacement}")
        elif event.type == pygame.KEYUP:
            current_disp = self.game.entity_manager.player.displacement
            if event.key in (pygame.K_w, pygame.K_s):
                self.game.entity_manager.player.displacement = (current_disp[0], 0)  # 重置垂直位移
                print(f"EventManager: 大廳 - 重置垂直位移為 {self.game.entity_manager.player.displacement}")
            elif event.key in (pygame.K_a, pygame.K_d):
                self.game.entity_manager.player.displacement = (0, current_disp[1])  # 重置水平位移
                print(f"EventManager: 大廳 - 重置水平位移為 {self.game.entity_manager.player.displacement}")

    def _handle_playing_event(self, event: pygame.event.Event) -> None:
        """處理遊戲進行狀態的事件。

        Args:
            event: Pygame 事件對象。

        處理玩家移動、技能切換和技能激活。
        """
        if self.game.menu_manager.current_menu:
            print(f"EventManager: 由於有活動菜單 {self.game.menu_manager.current_menu.__class__.__name__}，跳過事件 {event.type}")
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                self.game.entity_manager.player.switch_skill_chain((self.game.entity_manager.player.current_skill_chain_idx - 1) % self.game.entity_manager.player.max_skill_chains)  # 切換到上一個技能鏈
                print(f"EventManager: 遊戲中 - 切換技能鏈到 {self.game.entity_manager.player.current_skill_chain_idx}")
            elif event.key == pygame.K_e:
                self.game.entity_manager.player.switch_skill_chain((self.game.entity_manager.player.current_skill_chain_idx + 1) % self.game.entity_manager.player.max_skill_chains)  # 切換到下一個技能鏈
                print(f"EventManager: 遊戲中 - 切換技能鏈到 {self.game.entity_manager.player.current_skill_chain_idx}")
            elif event.key == pygame.K_SPACE:
                mouse_pos = pygame.mouse.get_pos()  # 獲取滑鼠位置
                target_pos = (mouse_pos[0] + self.game.render_manager.camera_offset[0], 
                             mouse_pos[1] + self.game.render_manager.camera_offset[1])  # 計算目標位置
                dx = target_pos[0] - self.game.entity_manager.player.x
                dy = target_pos[1] - self.game.entity_manager.player.y
                magnitude = math.sqrt(dx**2 + dy**2)  # 計算距離
                direction = (dx / magnitude, dy / magnitude) if magnitude > 0 else (0, 0)  # 計算方向向量
                self.game.entity_manager.player.activate_skill(direction, self.game.current_time, target_pos)  # 激活技能
                self.game.audio_manager.play_sound_effect("skill_activate")  # 播放技能音效
                print("EventManager: 遊戲中 - 激活技能")
            elif event.key == pygame.K_w:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], -1)  # 向上移動
                print(f"EventManager: 遊戲中 - 設置位移為 {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_s:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (current_disp[0], 1)  # 向下移動
                print(f"EventManager: 遊戲中 - 設置位移為 {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_a:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (-1, current_disp[1])  # 向左移動
                print(f"EventManager: 遊戲中 - 設置位移為 {self.game.entity_manager.player.displacement}")
            elif event.key == pygame.K_d:
                current_disp = self.game.entity_manager.player.displacement
                self.game.entity_manager.player.displacement = (1, current_disp[1])  # 向右移動
                print(f"EventManager: 遊戲中 - 設置位移為 {self.game.entity_manager.player.displacement}")
        elif event.type == pygame.KEYUP:
            current_disp = self.game.entity_manager.player.displacement
            if event.key in (pygame.K_w, pygame.K_s):
                self.game.entity_manager.player.displacement = (current_disp[0], 0)  # 重置垂直位移
                print(f"EventManager: 遊戲中 - 重置垂直位移為 {self.game.entity_manager.player.displacement}")
            elif event.key in (pygame.K_a, pygame.K_d):
                self.game.entity_manager.player.displacement = (0, current_disp[1])  # 重置水平位移
                print(f"EventManager: 遊戲中 - 重置水平位移為 {self.game.entity_manager.player.displacement}")

    def _handle_interaction(self) -> None:
        """處理與最近 NPC 的交互。

        尋找玩家範圍內最近的 NPC 並觸發交互。
        """
        if not self.game.entity_manager.player:
            return
        player = self.game.entity_manager.player
        nearest_npc = None
        min_distance = float('inf')
        for npc in self.game.entity_manager.npc_group:
            if hasattr(npc, 'interaction_range'):
                distance = npc.calculate_distance_to(player)  # 計算與玩家的距離
                if distance <= npc.interaction_range and distance < min_distance:
                    min_distance = distance
                    nearest_npc = npc
        if nearest_npc:
            nearest_npc.start_interaction()  # 觸發 NPC 交互
            print(f"EventManager: 與 {nearest_npc.tag} 交互")