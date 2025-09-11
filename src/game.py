import pygame
from src.dungeon_manager import DungeonManager
from src.event_manager import EventManager
from src.audio_manager import AudioManager
from src.render_manager import RenderManager
from src.storage_manager import StorageManager
from src.entity_manager import EntityManager
from src.menu_manager import MenuManager
from src.menu.menus.alchemy_menu import AlchemyMenu
from src.menu.menus.dungeon_menu import DungeonMenu
from src.menu.menus.crystal_menu import CrystalMenu
from src.menu.menus.main_menu import MainMenu
from src.menu.menus.setting_menu import SettingsMenu
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

class Game:
    def __init__(self, screen: pygame.Surface, pygame_clock: pygame.time.Clock):
        """初始化遊戲，設置核心組件和管理器。

        Args:
            screen: Pygame 的顯示表面，用於渲染畫面。
            pygame_clock: Pygame 的時鐘對象，用於控制幀率。
        """
        self.screen = screen  # 保存顯示表面
        self.clock = pygame_clock  # 保存時鐘對象
        self.current_time = 0.0  # 當前遊戲時間，初始為 0
        self.time_scale = 1.0  # 時間縮放因子，控制遊戲速度
        self.running = True  # 遊戲運行狀態
        self.dungeon_manager = DungeonManager(self)  # 初始化地牢管理器
        self.event_manager = EventManager(self)  # 初始化事件管理器
        self.audio_manager = AudioManager(self)  # 初始化音效管理器
        self.render_manager = RenderManager(self, screen)  # 初始化渲染管理器
        self.storage_manager = StorageManager(self)  # 初始化儲存管理器
        self.entity_manager = EntityManager(self)  # 初始化實體管理器
        self.menu_manager = MenuManager(self.screen, self)  # 初始化菜單管理器
        # 註冊菜單
        self.menu_manager.register_menu('main_menu', MainMenu())  # 主菜單
        self.menu_manager.register_menu('settings_menu', SettingsMenu())  # 設置菜單
        # 延遲註冊動態菜單
        self.menu_manager.register_menu('alchemy_menu', None)  # 煉金菜單
        self.menu_manager.register_menu('dungeon_menu', None)  # 地牢菜單
        self.menu_manager.register_menu('crystal_shop', None)  # 水晶商店
        # 設置初始菜單
        self.menu_manager.set_menu('main_menu')  # 顯示主菜單
        self.event_manager.state = "menu"  # 設置初始狀態為菜單
        print("Game: 已初始化，顯示主菜單")

    def start_game(self) -> None:
        """開始遊戲，初始化大廳和實體。

        初始化大廳房間並生成相關實體，進入大廳狀態。
        """
        print("Game: 正在初始化大廳")
        self.dungeon_manager.initialize_lobby()  # 初始化大廳
        lobby_room = self.dungeon_manager.get_current_room()  # 獲取大廳房間
        if lobby_room:
            print(f"Game: 大廳房間已初始化：{lobby_room}")
            self.entity_manager.initialize_lobby_entities(lobby_room)  # 初始化大廳實體
            self.event_manager.state = "lobby"  # 設置狀態為大廳
            self.menu_manager.set_menu(None)  # 隱藏菜單
            print("Game: 已進入大廳，無活動菜單")
        else:
            print("Game: 無法初始化大廳房間")

    def show_menu(self, menu_name: str, data: any = None) -> None:
        """顯示指定菜單。

        Args:
            menu_name: 要顯示的菜單名稱。
            data: 傳遞給菜單的可選數據，用於動態更新內容。

        根據菜單名稱動態註冊並顯示對應菜單。
        """
        print(f"Game: 顯示菜單 {menu_name}")
        if menu_name == 'alchemy_menu':
            self.menu_manager.register_menu(menu_name, AlchemyMenu(self, data or []))  # 註冊並顯示煉金菜單
        elif menu_name == 'dungeon_menu':
            self.menu_manager.register_menu(menu_name, DungeonMenu(self, data or []))  # 註冊並顯示地牢菜單
        elif menu_name == 'crystal_shop':
            self.menu_manager.register_menu(menu_name, CrystalMenu(self, data or {}))  # 註冊並顯示水晶商店
        elif menu_name == 'settings_menu':
            self.menu_manager.register_menu(menu_name, SettingsMenu())  # 註冊並顯示設置菜單
        self.menu_manager.set_menu(menu_name)  # 設置當前菜單
        self.event_manager.state = "menu"  # 設置狀態為菜單

    def hide_menu(self, menu_name: str) -> None:
        """隱藏指定菜單並返回大廳狀態或主菜單。

        Args:
            menu_name: 要隱藏的菜單名稱。

        如果當前菜單匹配，則隱藏並根據情況返回大廳或主菜單。
        """
        if self.menu_manager.current_menu and self.menu_manager.current_menu.__class__.__name__ == menu_name.capitalize():
            if menu_name == 'settings_menu':
                self.menu_manager.set_menu('main_menu')  # 返回主菜單
            else:
                self.menu_manager.set_menu(None)  # 隱藏菜單
                self.event_manager.state = "lobby"  # 返回大廳狀態
            print(f"Game: 已隱藏菜單 {menu_name}，當前菜單：{self.menu_manager.current_menu.__class__.__name__ if self.menu_manager.current_menu else 'None'}")
        else:
            print(f"Game: 無法隱藏菜單 {menu_name}，當前菜單：{self.menu_manager.current_menu.__class__.__name__ if self.menu_manager.current_menu else 'None'}")

    async def update(self, dt: float) -> bool:
        """更新遊戲狀態。

        Args:
            dt: 每幀的時間間隔（秒）。

        Returns:
            bool: 如果遊戲應繼續運行，返回 True；否則返回 False。

        處理事件、更新實體和攝影機，並根據遊戲狀態執行更新。
        """
        if not self.running:
            return False

        self.current_time += dt * self.time_scale  # 更新遊戲時間

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False  # 退出遊戲
                return False
            print(f"Game: 處理事件 {event.type}，狀態：{self.event_manager.state}，菜單：{self.menu_manager.current_menu.__class__.__name__ if self.menu_manager.current_menu else 'None'}")
            self.event_manager.handle_event(event)  # 處理事件

        if self.event_manager.state != "menu" or not self.menu_manager.current_menu:
            self.entity_manager.update(dt, self.current_time)  # 更新實體
            self.render_manager.update_camera(dt)  # 更新攝影機
            print(f"Game: 在狀態 {self.event_manager.state} 中更新實體和攝影機")
        else:
            print(f"Game: 由於有活動菜單，跳過實體和攝影機更新，狀態：{self.event_manager.state}")

        return True

    def draw(self) -> None:
        """根據當前遊戲狀態繪製畫面。

        根據 event_manager 的狀態調用對應的渲染方法。
        """
        print(f"Game: 繪製狀態 {self.event_manager.state}")
        if self.event_manager.state == "menu":
            self.render_manager.draw_menu()  # 繪製菜單
        elif self.event_manager.state == "skill_selection":
            self.render_manager.draw_skill_selection()  # 繪製技能選擇畫面
        elif self.event_manager.state == "lobby":
            self.render_manager.draw_lobby()  # 繪製大廳
        elif self.event_manager.state == "playing":
            self.render_manager.draw_playing()  # 繪製遊戲進行畫面
        elif self.event_manager.state == "win":
            self.render_manager.draw_win()  # 繪製勝利畫面

    async def run(self) -> None:
        """主遊戲循環，與 asyncio 兼容。

        控制遊戲的主循環，處理更新和繪製，直到遊戲結束。
        """
        print("Game: 已啟動，顯示主菜單")
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # 控制幀率為 60 FPS
            if not await self.update(dt):  # 更新遊戲狀態
                break
            self.draw()  # 繪製畫面
        pygame.quit()  # 退出 Pygame