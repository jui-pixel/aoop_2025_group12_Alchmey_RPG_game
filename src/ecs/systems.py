import esper
from .components import Position, Velocity

class MovementSystem(esper.Processor):
    def process(self, dt):
        for ent, (pos, vel) in self.world.get_components(Position, Velocity):
            pos.x += vel.x * dt
            pos.y += vel.y * dt