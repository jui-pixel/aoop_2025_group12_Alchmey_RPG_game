import pygame
import asyncio
import esper
from .config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from .event_bus import EventBus
from .state_machine import StateMachine
from .input import InputManager
from .resources import ResourceManager

# Systems will be imported here
# from ..ecs.systems.movement import MovementSystem
# from ..ecs.systems.render import RenderSystem

class Engine:
    """
    Main Game Engine.
    Manages the game loop, core subsystems, and the ECS world.
    """
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE if 'TITLE' in globals() else "Alchemy RPG")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Subsystems
        self.event_bus = EventBus()
        self.state_machine = StateMachine(initial_state="menu")
        self.input_manager = InputManager()
        self.resources = ResourceManager()
        
        # ECS World
        self.world = esper.World()
        
        # Monkey patch esper to allow systems to access engine (Architecture decision: convenience)
        # Ideally systems should be pure, but for migration compatibility we attach 'game' (engine)
        esper.game = self 
        
        # Placeholders for Managers that will be implemented in UI/Dungeon layers
        self.ui_manager = None 
        self.dungeon_manager = None
        
        self.dt = 0.0
        self.current_time = 0.0

    def setup_systems(self):
        """Initialize ECS systems here."""
        # self.world.add_processor(InputSystem())
        # self.world.add_processor(MovementSystem())
        # self.world.add_processor(RenderSystem())
        pass

    async def run(self):
        print("Engine: Starting game loop...")
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000.0
            self.current_time += self.dt
            
            # 1. Process Input
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                # Pass events to InputManager or UI
                # inputs = self.input_manager.process_events(events) 
                
                # Legacy EventManager compatibility stub if needed later
                if self.ui_manager:
                     pass # self.ui_manager.handle_event(event)

            # 2. Update based on State
            current_state = self.state_machine.state
            
            if current_state == "playing":
                # Run ECS Systems
                # We can filter which systems run based on logic if needed, or proper System logic does it
                # For now using generic process
                # esper.process(self.dt, screen=self.screen) # Arguments depend on System requirements
                pass
            elif current_state == "menu":
                if self.ui_manager:
                    # self.ui_manager.update(self.dt)
                    pass
            
            # 3. Render
            self.draw()
            
            await asyncio.sleep(0) # For async IO compatibility

        pygame.quit()

    def draw(self):
        self.screen.fill((0,0,0))
        
        # Draw game world if playing or background
        if self.state_machine.state == "playing":
             # RenderSystem should handle this in self.world.process() usually,
             # but if RenderSystem is a "Processor", it runs in the update loop.
             pass

        # Draw UI
        if self.ui_manager:
            # self.ui_manager.draw(self.screen)
            pass
            
        pygame.display.flip()
