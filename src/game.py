import pygame
from src.dungeon.dungeon_manager import DungeonManager
from src.event_manager import EventManager
from src.audio_manager import AudioManager
from src.render_manager import RenderManager
from src.storage_manager import StorageManager
from src.entity_manager import EntityManager
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class Game:
    def __init__(self, screen: pygame.Surface, pygame_clock: pygame.time.Clock):
        """Initialize the game with core components and managers."""
        self.screen = screen
        self.clock = pygame_clock
        self.current_time = 0.0
        self.time_scale = 1.0
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

    def run(self) -> None:
        """Main game loop."""
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0 * self.time_scale
            self.current_time += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.event_manager.handle_event(event)

            self.entity_manager.update(dt, self.current_time)
            self.render_manager.update_camera(dt)

            if self.event_manager.state == "menu":
                self.render_manager.draw_menu()
            elif self.event_manager.state == "skill_selection":
                self.render_manager.draw_skill_selection()
            elif self.event_manager.state == "weapon_selection":
                self.render_manager.draw_weapon_selection()
            elif self.event_manager.state == "lobby":
                self.render_manager.draw_lobby()
            elif self.event_manager.state == "playing":
                self.render_manager.draw_playing()
            elif self.event_manager.state == "win":
                self.render_manager.draw_win()

        pygame.quit()