# src/game.py 最終修正內容
import pygame
import esper # 引入 esper 模組
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from src.dungeon_manager import DungeonManager
from src.event_manager import EventManager
from src.audio_manager import AudioManager
from src.render_manager import RenderManager
from src.storage_manager import StorageManager
from src.entity_manager import EntityManager
from src.menu_manager import MenuManager

# 引入 ECS 系統（假設它們在 src.ecs.systems 中）
from src.ecs.systems import InputSystem, MovementSystem, CombatSystem, RenderSystem 

# 引入所有菜單類別
from src.menu.menus.alchemy_menu import AlchemyMenu
from src.menu.menus.amplifier_menu import AmplifierMenu
from src.menu.menus.amplifier_stat_menu import AmplifierStatMenu
from src.menu.menus.crystal_menu import CrystalMenu
from src.menu.menus.dungeon_menu import DungeonMenu
from src.menu.menus.element_menu import ElementMenu
from src.menu.menus.main_menu import MainMenu
from src.menu.menus.main_material_menu import MainMaterialMenu
from src.menu.menus.element_choose_menu import ElementChooseMenu
# 假設還需要 StatMenu, AmplifierChooseMenu, NamingMenu, SkillLibraryMenu, SkillChainEditMenu
# 請自行補齊缺少的 import
# 【補齊所有缺失的菜單類別】
from src.menu.menus.stat_menu import StatMenu
from src.menu.menus.amplifier_choose_menu import AmplifierChooseMenu
from src.menu.menus.naming_menu import NamingMenu
from src.menu.menus.skill_library_menu import SkillLibraryMenu
from src.menu.menus.skill_chain_edit_menu import SkillChainEditMenu
from src.menu.menus.skill_chain_menu import SkillChainMenu
from src.menu.menus.setting_menu import SettingsMenu # 假設 setting_menu.py 定義了 SettingsMenu 類

class Game:
    """遊戲主類別，管理所有遊戲狀態和子系統。"""
    
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        # 核心屬性
        self.screen = screen
        self.clock = clock
        self.running = True
        self.current_time = 0.0
        self.time_scale = 1.0 # 時間流逝速度
        self.world = esper
        # 管理器初始化
        self.event_manager = EventManager(self)
        self.audio_manager = AudioManager(self)
        self.dungeon_manager = DungeonManager(self)
        self.entity_manager = EntityManager(self)
        self.storage_manager = StorageManager(self)
        self.render_manager = RenderManager(self)
        self.menu_manager = MenuManager(self)
        self.menu_stack = []

        # --- ECS 初始化 (全域模式) ---
        # 修正: 將 Game 實例附加到 esper 模組上，供系統取用
        # 這樣系統就可以透過 esper.game.dungeon_manager 來取得地圖
        esper.game = self 
        
        # 註冊 ECS 系統 (使用全域註冊)
        esper.add_processor(InputSystem())
        esper.add_processor(MovementSystem())
        esper.add_processor(CombatSystem())
        # RenderSystem 通常在 draw 階段手動調用，或者設置為最低優先級
        esper.add_processor(RenderSystem())

        # 菜單註冊
        self.menu_manager.register_menu('main_menu', MainMenu(self))
        
        # --- NPC 交互菜單 (延遲初始化) ---
        self.menu_manager.register_menu('alchemy_menu', None) 
        self.menu_manager.register_menu('crystal_menu', None) 
        self.menu_manager.register_menu('dungeon_menu', None) 
        
        # --- 技能與天賦菜單 (延遲初始化) ---
        self.menu_manager.register_menu('skill_chain_menu', None)      # 新增
        self.menu_manager.register_menu('skill_chain_edit_menu', None) # 延遲初始化
        self.menu_manager.register_menu('skill_library_menu', None)    # 新增
        self.menu_manager.register_menu('stat_menu', None)             # 新增 (角色狀態)
        
        # --- 增幅器與元素相關菜單 (延遲初始化) ---
        self.menu_manager.register_menu('amplifier_menu', None) 
        self.menu_manager.register_menu('amplifier_stat_menu', None) 
        self.menu_manager.register_menu('amplifier_choose_menu', None)  # 新增
        self.menu_manager.register_menu('element_menu', None) 
        self.menu_manager.register_menu('element_choose_menu', None) 
        
        # --- 雜項與設置菜單 (延遲初始化) ---
        self.menu_manager.register_menu('main_material_menu', None) 
        self.menu_manager.register_menu('naming_menu', None)            # 新增
        self.menu_manager.register_menu('settings_menu', None)          # 使用 settings_menu.py 中假設的 SettingsMenu 類
        
        self.show_menu('main_menu') # 顯示主菜單

    def start_game(self) -> None:
        """開始遊戲，初始化大廳和實體。"""
        print("Game: 正在初始化大廳")
        self.dungeon_manager.initialize_lobby() # 初始化大廳
        lobby_room = self.dungeon_manager.get_current_room() # 獲取大廳房間
        if lobby_room:
            print(f"Game: 大廳房間已初始化：{lobby_room}")
            self.entity_manager.initialize_lobby_entities(lobby_room) # 初始化大廳實體
            self.event_manager.state = "lobby" # 設置狀態為大廳
            self.menu_manager.set_menu(None) # 隱藏菜單
            print("Game: 已進入大廳，無活動菜單")
        else:
            print("Game: 無法初始化大廳房間")
    
    def show_menu(self, menu_name: str, data = None, chain_idx: int = None) -> None:
        """Show the specified menu and hide the current one if active. (包含延遲初始化)"""
        if self.menu_manager.current_menu:
            # 將當前菜單推入堆棧 (如果需要返回的話)
            self.menu_stack.append(self.menu_manager.current_menu.__class__.__name__.lower())
        
        if menu_name in self.menu_manager.menus:
            # 1. 延遲初始化檢查
            if self.menu_manager.menus[menu_name] is None:
                print(f"Game: 正在延遲初始化菜單: {menu_name}")
                
                new_menu_instance = None
                
                if menu_name == 'alchemy_menu':
                    new_menu_instance = AlchemyMenu(self, data)
                elif menu_name == 'amplifier_menu':
                    new_menu_instance = AmplifierMenu(self, data)
                elif menu_name == 'amplifier_stat_menu':
                    new_menu_instance = AmplifierStatMenu(self, data)
                elif menu_name == 'crystal_menu':
                    new_menu_instance = CrystalMenu(self, data)
                elif menu_name == 'dungeon_menu':
                    new_menu_instance = DungeonMenu(self, data)
                elif menu_name == 'element_menu':
                    new_menu_instance = ElementMenu(self, data)
                elif menu_name == 'main_material_menu':
                    new_menu_instance = MainMaterialMenu(self, data)
                elif menu_name == 'element_choose_menu':
                    new_menu_instance = ElementChooseMenu(self, data)
                
                # 【補齊其他菜單的延遲初始化】
                elif menu_name == 'stat_menu':
                    new_menu_instance = StatMenu(self, data)
                elif menu_name == 'amplifier_choose_menu':
                    new_menu_instance = AmplifierChooseMenu(self, data)
                elif menu_name == 'naming_menu':
                    new_menu_instance = NamingMenu(self, data)
                elif menu_name == 'skill_library_menu':
                    new_menu_instance = SkillLibraryMenu(self, data)
                elif menu_name == 'settings_menu':
                    new_menu_instance = SettingsMenu(self, data)
                
                # 特殊情況：skill_chain_edit_menu 需要 chain_idx
                elif menu_name == 'skill_chain_edit_menu' and chain_idx is not None:
                    new_menu_instance = SkillChainEditMenu(self, chain_idx)
                
                # 將新實例註冊到 MenuManager
                if new_menu_instance:
                    self.menu_manager.menus[menu_name] = new_menu_instance
                else:
                    print(f"Game: 錯誤！菜單 {menu_name} 缺少必要參數 (如 chain_idx) 或未被定義初始化邏輯。")
                    return # 中止執行

            # 2. 更新需要特殊數據的菜單 (例如 SkillChainEditMenu)
            if menu_name == 'skill_chain_edit_menu' and chain_idx is not None:
                # 假設此時菜單已被初始化 (無論是延遲還是預先)
                menu = self.menu_manager.menus[menu_name]
                menu.chain_idx = chain_idx
                
                # 這裡假設 self.entity_manager.player 存在且結構正確
                player_comp = self.entity_manager.get_player_component() 
                if player_comp:
                    menu.slots = player_comp.skill_chain[chain_idx][:]
                    # 填充剩餘空位
                    menu.slots += [None] * (8 - len(menu.slots))
                    menu._update_buttons()
                else:
                    print("Game: 警告！嘗試編輯技能鏈時找不到 Player Component。")

            # 3. 切換到新菜單
            self.menu_manager.set_menu(menu_name)
        else:
            print(f"Game: 警告！嘗試顯示未註冊的菜單名稱: {menu_name}")
            
        print(f"Game: 已顯示菜單 {menu_name}，當前菜單：{self.menu_manager.current_menu.__class__.__name__ if self.menu_manager.current_menu else 'None'}")

    def hide_menu(self, menu_name: str) -> None:
        """Hide the specified menu and return to the previous one if available."""
        if self.menu_manager.current_menu and self.menu_manager.current_menu.__class__.__name__.lower() == menu_name:
            self.menu_manager.set_menu(None)
            print(f"Game: 已隱藏菜單 {menu_name}")
            # 從堆棧彈出上一個菜單（如果有的話）
            if self.menu_stack:
                previous_menu = self.menu_stack.pop()
                self.show_menu(previous_menu)
        else:
            print(f"Game: 嘗試隱藏非當前活動菜單 {menu_name}，當前菜單為 {self.menu_manager.current_menu.__class__.__name__ if self.menu_manager.current_menu else 'None'}")

    async def update(self, dt: float) -> bool:
        """
        核心遊戲更新邏輯。
        處理事件、更新實體和攝影機，並根據遊戲狀態執行更新。
        """
        if not self.running:
            return False

        self.current_time += dt * self.time_scale # 更新遊戲時間

        # 處理 Pygame 事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            # 將事件傳遞給 EventManager 處理 (包括菜單輸入)
            self.event_manager.handle_event(event)

        # 根據遊戲狀態更新邏輯
        state = self.event_manager.state
        if state == "menu" and self.menu_manager.current_menu:
            # 菜單模式：只更新菜單
            self.menu_manager.current_menu.update(dt)
        elif state in ["lobby", "playing", "skill_selection"]:
            # 遊戲模式：更新 ECS 系統和攝影機
            
            # --- ECS 更新 ---
            # 修正: 呼叫全域的 esper.process() 函式，並傳遞必要的參數
            # 這裡傳遞 screen 和 camera_offset 是因為 RenderSystem 需要它們
            esper.process(dt,
                          screen=self.screen,
                          camera_offset=self.render_manager.camera_offset)
            
            # 攝影機更新 (RenderManager 應該處理)
            self.render_manager.update_camera(dt)
            
        elif state == "win":
            pass # 勝利狀態，等待用戶輸入或過場動畫

        return self.running

    def draw(self) -> None:
        """根據當前遊戲狀態繪製畫面。"""
        self.screen.fill((0, 0, 0)) # 清空畫面
        
        state = self.event_manager.state
        # print(f"Game: 繪製狀態 {state}") # 避免在主循環中頻繁打印
        
        if state == "menu":
            self.render_manager.draw_menu() # 繪製菜單
        elif state == "skill_selection":
            self.render_manager.draw_skill_selection() # 繪製技能選擇畫面
        elif state == "lobby":
            self.render_manager.draw_lobby() # 繪製大廳
        elif state == "playing":
            self.render_manager.draw_playing() # 繪製遊戲進行畫面
        elif state == "win":
            self.render_manager.draw_win() # 繪製勝利畫面
        
        pygame.display.flip()

    async def run(self) -> None:
        """主遊戲循環，與 asyncio 兼容。"""
        print("Game: 已啟動，顯示主菜單")
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0 # 控制幀率為 60 FPS
            if not await self.update(dt): # 更新遊戲狀態
                break
            self.draw() # 繪製畫面
        
        pygame.quit() # 退出 Pygame