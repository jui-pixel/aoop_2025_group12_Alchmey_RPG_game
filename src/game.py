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
from src.menu.menus.settings_menu import SettingsMenu
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class Game:
    def __init__(self, screen: pygame.Surface, pygame_clock: pygame.time.Clock):
        """Initialize the game with core components and managers."""
        self.screen = screen
        self.clock = pygame_clock
        self.current_time = 0.0
        self.time_scale = 1.0
        self.running = True
        self.dungeon_manager = DungeonManager(self)
        self.event_manager = EventManager(self)
        self.audio_manager = AudioManager(self)
        self.render_manager = RenderManager(self, screen)
        self.storage_manager = StorageManager(self)
        self.entity_manager = EntityManager(self)
        self.menu_manager = MenuManager(self.screen, self)
        # Register menus
        self.menu_manager.register_menu('main_menu', MainMenu())
        self.menu_manager.register_menu('settings_menu', SettingsMenu())
        # 延遲註冊動態選單，直到需要時創建
        self.menu_manager.register_menu('alchemy_menu', None)
        self.menu_manager.register_menu('dungeon_menu', None)
        self.menu_manager.register_menu('crystal_shop', None)
        # 設置初始選單
        self.menu_manager.set_menu('main_menu')
        self.event_manager.state = "menu"
        print("Game: Initialized, showing main_menu")

    def start_game(self) -> None:
        """Start the game by initializing the lobby and entities."""
        print("Game: Initializing lobby")
        self.dungeon_manager.initialize_lobby()
        lobby_room = self.dungeon_manager.get_current_room()
        if lobby_room:
            print(f"Game: Lobby room initialized: {lobby_room}")
            self.entity_manager.initialize_lobby_entities(lobby_room)
            self.event_manager.state = "lobby"
            self.menu_manager.set_menu(None)
            print("Game: Entered lobby, no menu active")
        else:
            print("Game: Failed to initialize lobby room")

    def show_menu(self, menu_name: str, data: any = None) -> None:
        """Show a specific menu with optional data to update its content."""
        print(f"Game: Showing menu {menu_name}")
        if menu_name == 'alchemy_menu':
            self.menu_manager.register_menu(menu_name, AlchemyMenu(self, data or []))
        elif menu_name == 'dungeon_menu':
            self.menu_manager.register_menu(menu_name, DungeonMenu(self, data or []))
        elif menu_name == 'crystal_shop':
            self.menu_manager.register_menu(menu_name, CrystalMenu(self, data or {}))
        elif menu_name == 'settings_menu':
            self.menu_manager.register_menu(menu_name, SettingsMenu())
        self.menu_manager.set_menu(menu_name)
        self.event_manager.state = "menu"

    def hide_menu(self, menu_name: str) -> None:
        """Hide a specific menu and return to lobby state or main menu."""
        if self.menu_manager.current_menu and self.menu_manager.current_menu.__class__.__name__ == menu_name.capitalize():
            if menu_name == 'settings_menu':
                self.menu_manager.set_menu('main_menu')
            else:
                self.menu_manager.set_menu(None)
                self.event_manager.state = "lobby"
            print(f"Game: Hid menu {menu_name}, current menu: {self.menu_manager.current_menu.__class__.__name__ if self.menu_manager.current_menu else 'None'}")
        else:
            print(f"Game: Failed to hide menu {menu_name}, current menu: {self.menu_manager.current_menu.__class__.__name__ if self.menu_manager.current_menu else 'None'}")

    async def update(self, dt: float) -> bool:
        """Update game state, return False to stop the game."""
        if not self.running:
            return False

        self.current_time += dt * self.time_scale

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            print(f"Game: Processing event {event.type}")
            self.event_manager.handle_event(event)

        if self.event_manager.state != "menu":
            self.entity_manager.update(dt, self.current_time)
            self.render_manager.update_camera(dt)

        return True

    def draw(self) -> None:
        """Draw the current game state."""
        print(f"Game: Drawing state {self.event_manager.state}")
        if self.event_manager.state == "menu":
            self.render_manager.draw_menu()
        elif self.event_manager.state == "skill_selection":
            self.render_manager.draw_skill_selection()
        elif self.event_manager.state == "lobby":
            self.render_manager.draw_lobby()
        elif self.event_manager.state == "playing":
            self.render_manager.draw_playing()
        elif self.event_manager.state == "win":
            self.render_manager.draw_win()

    async def run(self) -> None:
        """Main game loop, compatible with asyncio."""
        print("Game: Started, showing main_menu")
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            if not await self.update(dt):
                break
            self.draw()
        pygame.quit()