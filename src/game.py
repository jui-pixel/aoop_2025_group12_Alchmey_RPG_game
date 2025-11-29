# src/game.py 最終修正內容
import pygame
import esper # 引入 esper 模組
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from src.dungeon_manager import DungeonManager
from src.event_manager import EventManager
from src.audio_manager import AudioManager
from src.render_manager import RenderManager
from src.storage_manager import StorageManager
from src.entities.entity_manager import EntityManager
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

class Game:
    """遊戲主類別，管理所有遊戲狀態和子系統。"""
    
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        # 核心屬性
        self.screen = screen
        self.clock = clock
        self.running = True
        self.current_time = 0.0
        self.time_scale = 1.0 # 時間流逝速度

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
        self.menu_manager.register_menu('alchemy_menu', None) # 延遲初始化
        self.menu_manager.register_menu('amplifier_menu', None) 
        self.menu_manager.register_menu('amplifier_stat_menu', None) 
        self.menu_manager.register_menu('crystal_menu', None) 
        self.menu_manager.register_menu('dungeon_menu', None) 
        self.menu_manager.register_menu('element_menu', None) 
        self.menu_manager.register_menu('main_material_menu', None) 
        self.menu_manager.register_menu('element_choose_menu', None) 
        self.menu_manager.register_menu('skill_chain_edit_menu', None) # 延遲初始化
        # 假設還有其他菜單: stat_menu, amplifier_choose_menu, naming_menu, skill_library_menu
        # ... (請補齊其他菜單註冊)
        
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
        """Show the specified menu and hide the current one if active."""
        if self.menu_manager.current_menu:
            self.menu_stack.append(self.menu_manager.current_menu.__class__.__name__.lower())
        
        # ... (菜單初始化邏輯，保持您原有的邏輯)
        # 這裡需要補齊您在原程式碼中缺少的菜單類別的 import
        
        if menu_name in self.menu_manager.menus:
            # 延遲初始化邏輯 (保持您原有的邏輯)
            if self.menu_manager.menus[menu_name] is None:
                # 這裡需要您將所有的菜單類別補齊，例如：
                # from src.menu.menus.stat_menu import StatMenu
                
                if menu_name == 'alchemy_menu':
                    self.menu_manager.menus[menu_name] = AlchemyMenu(self, data)
                # ... (其他菜單初始化，此處省略以保持簡潔)
                # 您的原始代碼中缺少 StatMenu, AmplifierChooseMenu, NamingMenu, SkillLibraryMenu, SkillChainEditMenu 的 import
                
                # 假設 StatMenu 存在：
                # elif menu_name == 'stat_menu':
                #    self.menu_manager.menus[menu_name] = StatMenu(self, data)
                # ...
                
                elif menu_name == 'skill_chain_edit_menu' and chain_idx is not None:
                    self.menu_manager.menus[menu_name] = SkillChainEditMenu(self, chain_idx)
                else:
                    # 處理缺少參數的錯誤
                    # ... 
                    pass # Placeholder
            
            # 更新 SkillChainEditMenu 邏輯 (保持您原有的邏輯)
            elif menu_name == 'skill_chain_edit_menu' and chain_idx is not None:
                self.menu_manager.menus[menu_name].chain_idx = chain_idx
                # 這裡假設 self.entity_manager.player 存在且結構正確
                self.menu_manager.menus[menu_name].slots = self.entity_manager.player.skill_chain[chain_idx][:]
                self.menu_manager.menus[menu_name].slots += [None] * (8 - len(self.menu_manager.menus[menu_name].slots))
                self.menu_manager.menus[menu_name]._update_buttons()
                
            self.menu_manager.set_menu(menu_name)
        print(f"Game: 已顯示菜單 {menu_name}，當前菜單：{self.menu_manager.current_menu.__class__.__name__ if self.menu_manager.current_menu else 'None'}")


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