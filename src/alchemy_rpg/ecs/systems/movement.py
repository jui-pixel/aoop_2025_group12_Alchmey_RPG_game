import esper
from ..components.common import Position, Velocity
from ...core.config import TILE_SIZE, PASSABLE_TILES

class MovementSystem(esper.Processor):
    def process(self, *args, **kwargs):
        dt = args[0] if args else 0.0
        
        for ent, (pos, vel) in self.world.get_components(Position, Velocity):
            if vel.x == 0 and vel.y == 0:
                continue
            
            # Simple movement logic for now
            # Collision detection logic would go here, interacting with Dungeon layer
            
            new_x = pos.x + vel.x * dt
            new_y = pos.y + vel.y * dt
            
            pos.x = new_x
            pos.y = new_y
