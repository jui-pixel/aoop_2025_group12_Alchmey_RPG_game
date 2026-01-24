import esper

class World(esper.World):
    """
    ECS Registry.
    Manages Entity IDs and Component mapping.
    Extends esper.World.
    """
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        # In esper, self._entities, self._components etc manage the mapping.
