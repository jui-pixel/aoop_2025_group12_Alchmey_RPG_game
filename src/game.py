import pygame
from .dungeon_manager import DungeonManager
from .event_manager import EventManager
from .audio_manager import AudioManager
from .render_manager import RenderManager
from .storage_manager import StorageManager
from .entity_manager import EntityManager
from .menu_manager import MenuManager
from .menu.menus.alchemy_menu import AlchemyMenu
from .menu.menus.dungeon_menu import DungeonMenu
from .menu.menus.crystal_menu import CrystalMenu
from .menu.menus.main_menu import MainMenu
from .config import SCREEN_WIDTH, SCREEN_HEIGHT

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
        self.menu_manager.register_menu('alchemy_menu', AlchemyMenu(self, []))
        self.menu_manager.register_menu('dungeon_menu', DungeonMenu(self, []))
        self.menu_manager.register_menu('crystal_shop', CrystalMenu(self, {}))

    def start_game(self) -> None:
        """Start the game by initializing the lobby and entities."""
        self.dungeon_manager.initialize_lobby()
        lobby_room = self.dungeon_manager.get_current_room()
        self.entity_manager.initialize_lobby_entities(lobby_room)
        self.event_manager.state = "lobby"

    def show_menu(self, menu_name: str, data: any = None) -> None:
        """Show a specific menu with optional data to update its content."""
        if menu_name == 'alchemy_menu':
            self.menu_manager.register_menu(menu_name, AlchemyMenu(self, data))
        elif menu_name == 'dungeon_menu':
            self.menu_manager.register_menu(menu_name, DungeonMenu(self, data))
        elif menu_name == 'crystal_shop':
            self.menu_manager.register_menu(menu_name, CrystalMenu(self, data))
        self.menu_manager.set_menu(menu_name)
        self.event_manager.state = "menu"

    def hide_menu(self, menu_name: str) -> None:
        """Hide a specific menu and return to lobby state."""
        self.menu_manager.set_menu(None)
        self.event_manager.state = "lobby"

    async def update(self, dt: float) -> bool:
        """Update game state, return False to stop the game."""
        if not self.running:
            return False

        self.current_time += dt * self.time_scale

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            self.event_manager.handle_event(event)

        self.entity_manager.update(dt, self.current_time)
        self.render_manager.update_camera(dt)

        return True

    def draw(self) -> None:
        """Draw the current game state."""
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
        self.start_game()
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            if not await self.update(dt):
                break
            self.draw()
        pygame.quit()