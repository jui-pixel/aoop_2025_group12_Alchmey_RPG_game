import pygame
from .dungeon_manager import DungeonManager
from .event_manager import EventManager
from .audio_manager import AudioManager
from .render_manager import RenderManager
from .storage_manager import StorageManager
from .entity_manager import EntityManager
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

    def start_game(self) -> None:
        """Start the game by initializing the lobby and player."""
        self.dungeon_manager.initialize_lobby()
        lobby_room = self.dungeon_manager.get_current_room()
        center_x, center_y = self.dungeon_manager.get_room_center(lobby_room)
        self.entity_manager.initialize_player(center_x, center_y)
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