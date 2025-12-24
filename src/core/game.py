# src/game.py 最終修正內容
import pygame
import esper # 引入 esper 模組
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
import src.manager

# 引入 ECS 系統（假設它們在 src.ecs.systems 中）
from src.ecs.systems import (
    InputSystem, MovementSystem, CombatSystem, RenderSystem, 
    HealthSystem, BuffSystem, EnergySystem, AISystem, TimerSystem
)
from src.menu.menus.main_menu import MainMenu
class Game:
    """遊戲主類別，管理所有遊戲狀態和子系統。"""
    
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        # 核心屬性
        self.screen = screen
        self.clock = clock
        self.running = True
        self.current_time = 0.0
        self.dt = 0.0
        self.time_scale = 1.0 # 時間流逝速度
        self.world = esper
        # 管理器初始化
        self.event_manager = src.manager.EventManager(self)
        self.audio_manager = src.manager.AudioManager(self)
        self.dungeon_manager = src.manager.DungeonManager(self)
        self.entity_manager = src.manager.EntityManager(self)
        self.storage_manager = src.manager.StorageManager(self)
        self.render_manager = src.manager.RenderManager(self)
        self.menu_manager = src.manager.MenuManager(self)

        # --- ECS 初始化 (全域模式) ---
        # 修正: 將 Game 實例附加到 esper 模組上，供系統取用
        esper.game = self 
        
        # 註冊 ECS 系統 (使用全域註冊)
        self.world.add_processor(InputSystem())
        self.world.add_processor(AISystem(self))

        self.world.add_processor(MovementSystem())
        self.world.add_processor(CombatSystem())
        self.world.add_processor(HealthSystem())
        self.world.add_processor(BuffSystem())
        self.world.add_processor(EnergySystem())
        self.world.add_processor(TimerSystem())
        self.world.add_processor(RenderSystem())

        # 菜單註冊
        self.menu_manager.register_menu('main_menu', MainMenu(self))
        
        # --- NPC 交互菜單 (延遲初始化) ---
        self.menu_manager.register_menu('alchemy_menu', None) 
        self.menu_manager.register_menu('crystal_menu', None) 
        self.menu_manager.register_menu('dungeon_menu', None) 
        
        # --- 技能與天賦菜單 (延遲初始化) ---
        self.menu_manager.register_menu('skill_chain_menu', None)        # 新增
        self.menu_manager.register_menu('skill_chain_edit_menu', None) # 延遲初始化
        self.menu_manager.register_menu('skill_library_menu', None)     # 新增
        self.menu_manager.register_menu('stat_menu', None)              # 新增 (角色狀態)
        
        # --- 增幅器與元素相關菜單 (延遲初始化) ---
        self.menu_manager.register_menu('amplifier_menu', None) 
        self.menu_manager.register_menu('amplifier_stat_menu', None) 
        self.menu_manager.register_menu('amplifier_choose_menu', None)  # 新增
        self.menu_manager.register_menu('element_menu', None) 
        self.menu_manager.register_menu('element_choose_menu', None) 
        
        # --- 雜項與設置菜單 (延遲初始化) ---
        self.menu_manager.register_menu('main_material_menu', None) 
        self.menu_manager.register_menu('naming_menu', None)             # 新增
        self.menu_manager.register_menu('settings_menu', None)          # 使用 settings_menu.py 中假設的 SettingsMenu 類
        self.menu_manager.register_menu('win_menu', None)
        self.menu_manager.register_menu('death_menu', None)  
        self.menu_manager.open_menu('main_menu') # 顯示主菜單

    def start_game(self) -> None:
        """開始遊戲，初始化大廳和實體。"""
        print("Game: 正在初始化大廳")
        self.dungeon_manager.initialize_lobby() # 初始化大廳
        lobby_room = self.dungeon_manager.get_current_room() # 獲取大廳房間
        if lobby_room:
            print(f"Game: 大廳房間已初始化：{lobby_room}")
            self.entity_manager.initialize_lobby_entities(lobby_room) # 初始化大廳實體
            self.event_manager.state = "lobby" # 設置狀態為大廳
            # 切換到遊戲狀態時，清空菜單堆棧 (使用 set_menu(None) 達到清空效果)
            self.menu_manager.set_menu(None) 
            print("Game: 已進入大廳，無活動菜單")
        else:
            print("Game: 無法初始化大廳房間")
    
    # def show_menu(self, menu_name: str, data = None, chain_idx: int = None) -> None:
    #     """
    #     顯示指定的菜單。
    #     使用 MenuManager.push_menu 實現菜單疊加。
        
    #     Args:
    #         menu_name: 要顯示的菜單名稱。
    #         data: 傳遞給菜單的初始化或更新數據。
    #         chain_idx: 僅用於 skill_chain_edit_menu 的特殊參數。
    #     """
    #     # 1. 延遲初始化檢查 (與舊邏輯相同)
    #     if menu_name in self.menu_manager.menus:
    #         if self.menu_manager.menus[menu_name] is None:
    #             print(f"Game: 正在延遲初始化菜單: {menu_name}")
                
    #             new_menu_instance = None
                
    #             # --- 菜單實例化邏輯 (保留不變) ---
    #             if menu_name == 'alchemy_menu':
    #                 new_menu_instance = AlchemyMenu(self, data)
    #             elif menu_name == 'amplifier_menu':
    #                 new_menu_instance = AmplifierMenu(self, data)
    #             elif menu_name == 'amplifier_stat_menu':
    #                 new_menu_instance = AmplifierStatMenu(self, data)
    #             elif menu_name == 'crystal_menu':
    #                 new_menu_instance = CrystalMenu(self, data)
    #             elif menu_name == 'dungeon_menu':
    #                 # 【修正點】解包 data 並將其傳遞給 DungeonMenu
    #                 dungeons = data.get('dungeons', []) if isinstance(data, dict) else data 
    #                 npc_facade = data.get('npc_facade') if isinstance(data, dict) else None
                    
    #                 if not isinstance(dungeons, list):
    #                     dungeons = data 
    #                     npc_facade = None 

    #                 new_menu_instance = DungeonMenu(self, dungeons, npc_facade)
    #             elif menu_name == 'element_menu':
    #                 new_menu_instance = ElementMenu(self, data)
    #             elif menu_name == 'main_material_menu':
    #                 new_menu_instance = MainMaterialMenu(self, data)
    #             elif menu_name == 'element_choose_menu':
    #                 new_menu_instance = ElementChooseMenu(self, data)
                
    #             # 【補齊其他菜單的延遲初始化】
    #             elif menu_name == 'stat_menu':
    #                 new_menu_instance = StatMenu(self, data)
    #             elif menu_name == 'amplifier_choose_menu':
    #                 new_menu_instance = AmplifierChooseMenu(self, data)
    #             elif menu_name == 'naming_menu':
    #                 new_menu_instance = NamingMenu(self, data)
    #             elif menu_name == 'skill_library_menu':
    #                 new_menu_instance = SkillLibraryMenu(self, data)
    #             elif menu_name == 'settings_menu':
    #                 new_menu_instance = SettingsMenu(self, data)
    #             elif menu_name == 'skill_chain_menu':
    #                 new_menu_instance = SkillChainMenu(self, data)
    #             # 特殊情況：skill_chain_edit_menu 需要 chain_idx
    #             elif menu_name == 'skill_chain_edit_menu' and chain_idx is not None:
    #                 new_menu_instance = SkillChainEditMenu(self, chain_idx)
                
    #             # 將新實例註冊到 MenuManager
    #             if new_menu_instance:
    #                 self.menu_manager.menus[menu_name] = new_menu_instance
    #             else:
    #                 print(f"Game: 錯誤！菜單 {menu_name} 缺少必要參數 (如 chain_idx) 或未被定義初始化邏輯。")
    #                 return # 中止執行

    #         # 2. 更新需要特殊數據的菜單 (與舊邏輯相同)
    #         if menu_name == 'skill_chain_edit_menu' and chain_idx is not None:
    #             menu = self.menu_manager.menus[menu_name]
    #             menu.chain_idx = chain_idx
                
    #             player_comp = self.entity_manager.get_player_component() 
    #             if player_comp:
    #                 menu.slots = player_comp.skill_chain[chain_idx][:]
    #                 menu.slots += [None] * (8 - len(menu.slots))
    #                 menu._update_buttons()
    #             else:
    #                 print("Game: 警告！嘗試編輯技能鏈時找不到 Player Component。")
    #         elif menu_name == 'dungeon_menu':
    #             menu = self.menu_manager.menus[menu_name]
    #             if isinstance(data, dict) and 'npc_facade' in data:
    #                 menu.update_npc_facade(data['npc_facade'])
                    
    #         # 3. 推入新菜單 (使用新的 push_menu)
    #         self.menu_manager.push_menu(menu_name) # <-- 修正點：使用 push_menu 實現疊加
    #     else:
    #         print(f"Game: 警告！嘗試顯示未註冊的菜單名稱: {menu_name}")
        
    #     self.event_manager.state = "menu" # 切換到菜單狀態
    #     print(f"Game: 已顯示菜單 {menu_name}，激活菜單數：{len(self.menu_manager.active_menus)}")

    # def hide_menu(self, menu_name: str) -> None:
    #     """
    #     隱藏指定的菜單。
    #     由於採用堆棧模式，此方法僅負責彈出頂層菜單。
        
    #     Args:
    #         menu_name: 期望隱藏的菜單名稱 (用於檢查)。
    #     """
    #     current_top_menu = self.menu_manager.get_current_menu()
        
    #     # 僅在頂層菜單確實是我們想要隱藏的菜單時才執行 pop
    #     if current_top_menu and current_top_menu.__class__.__name__.lower() == menu_name:
    #         self.menu_manager.pop_menu() # <-- 修正點：使用 pop_menu 實現返回上一層
    #         print(f"Game: 已隱藏菜單 {menu_name}")
    #         if not self.menu_manager.get_current_menu():
    #             self.event_manager.state = "playing" # 無活動菜單時返回遊戲狀態
    #             print("Game: 菜單堆棧為空，返回遊戲狀態")
            
    #     elif current_top_menu is None:
    #         print(f"Game: 嘗試隱藏菜單 {menu_name}，但菜單堆棧為空。")
            
    #     else:
    #         print(f"Game: 警告！嘗試隱藏菜單 {menu_name}，但當前頂層菜單為 {current_top_menu.__class__.__name__}，不執行操作。")

    async def update(self, dt: float) -> bool:
        """
        核心遊戲更新邏輯。
        處理事件、更新實體和攝影機，並根據遊戲狀態執行更新。
        """
        if not self.running:
            return False
        self.dt = dt
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
        if self.menu_manager.active_menus:
            # 菜單模式：只更新菜單
            self.menu_manager.update_current_menus(dt)
        else:
            # 遊戲模式：更新 ECS 系統和攝影機
            
            # --- ECS 更新 ---
            # 修正: 呼叫全域的 esper.process() 函式，並傳遞必要的參數
            # 這裡傳遞 screen 和 camera_offset 是因為 RenderSystem 需要它們
            esper.process(dt,
                          screen=self.screen,
                          camera_offset=self.render_manager.camera_offset, current_time=self.current_time, game=self)
            
            # 攝影機更新 (RenderManager 應該處理)
            self.render_manager.update_camera(dt)
            
        # elif state == "win":
        #     pass # 勝利狀態，等待用戶輸入或過場動畫

        return self.running
    
    async def run(self) -> None:
        """主遊戲循環，與 asyncio 兼容。"""
        print("Game: 已啟動，顯示主菜單")
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0 # 控制幀率為 60 FPS
            if not await self.update(dt): # 更新遊戲狀態
                break
            self.draw() # 繪製畫面
        
        pygame.quit() # 退出 Pygame
    
    def draw(self) -> None:
        """根據當前遊戲狀態繪製畫面。"""
        self.screen.fill((0, 0, 0)) # 清空畫面
        
        # state = self.event_manager.state
        # # print(f"Game: 繪製狀態 {state}") # 避免在主循環中頻繁打印
        # if not self.menu_manager.active_menus:
        #     self.event_manager.state = "playing" # 無活動菜單時返回遊戲狀態
        # if state == "menu":
        #     self.render_manager.draw_menu() # 繪製菜單
        # elif state == "lobby":
        #     self.render_manager.draw_lobby() # 繪製大廳
        # elif state == "playing":
        #     self.render_manager.draw_playing() # 繪製遊戲進行畫面
        # elif state == "win":
        #     self.render_manager.draw_win() # 繪製勝利畫面
        
        if self.menu_manager.active_menus:
            self.render_manager.draw_menu() # 繪製菜單
        else:
            self.render_manager.draw_playing() # 繪製遊戲進行畫面
        
        pygame.display.flip()
    
    def on_player_death(self) -> None:
        """處理玩家死亡邏輯，顯示死亡菜單並重置遊戲狀態。"""
        print("Game: 玩家已死亡，顯示死亡菜單")
        self.menu_manager.open_menu('death_menu') # 顯示死亡菜單
        # 其他死亡處理邏輯（如重置遊戲等）可在此添加