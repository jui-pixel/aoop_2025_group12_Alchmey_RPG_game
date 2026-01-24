import esper
import pygame
from ..components.common import Position, Renderable
from ...core.config import SCREEN_WIDTH, SCREEN_HEIGHT

class RenderSystem(esper.Processor):
    def process(self, *args, **kwargs):
        # Expect 'screen' and 'camera_offset' in kwargs or args
        screen =  kwargs.get('screen')
        camera_offset = kwargs.get('camera_offset', (0, 0)) # Default to no offset
        
        if not screen:
            return

        render_list = []
        for ent, (pos, rend) in self.world.get_components(Position, Renderable):
            if not rend.visible:
                continue
            render_list.append((pos, rend))
            
        # Sort by layer
        render_list.sort(key=lambda x: x[1].layer)
        
        for pos, rend in render_list:
            screen_x = pos.x - camera_offset[0]
            screen_y = pos.y - camera_offset[1]
            
            # Simple cull
            if (screen_x + rend.w < 0 or screen_x > SCREEN_WIDTH or 
                screen_y + rend.h < 0 or screen_y > SCREEN_HEIGHT):
                continue
                
            if rend.image:
                screen.blit(rend.image, (screen_x, screen_y))
            else:
                pygame.draw.rect(screen, rend.color, (screen_x, screen_y, rend.w, rend.h))
