from typing import List, Callable, Any, Dict
from .context import DungeonContext

# Type hint for a pipeline step function
# Each step takes context, modifies it, and returns it
PipelineStep = Callable[[DungeonContext], DungeonContext]

class DungeonPipeline:
    """
    依序執行地牢生成步驟的管線。
    """
    def __init__(self):
        self.steps: List[PipelineStep] = []
        
    def add_step(self, step: PipelineStep) -> 'DungeonPipeline':
        """Add a step to the pipeline (fluent interface)."""
        self.steps.append(step)
        return self
    
    def execute(self, context: DungeonContext) -> DungeonContext:
        """Execute all steps in order."""
        for step in self.steps:
            context = step(context)
        return context

# Example step functions

def step_initialize_grid(context: DungeonContext) -> DungeonContext:
    """Initialize the grid with default tiles."""
    context.grid = [['Outside' for _ in range(context.grid_width)] 
                    for _ in range(context.grid_height)]
    return context

def step_generate_bsp(context: DungeonContext) -> DungeonContext:
    """Generate BSP tree structure."""
    # Placeholder: would call BSPGenerator
    # from .algorithms.bsp import BSPGenerator
    # context.bsp_root = BSPGenerator().generate(context.grid_width, context.grid_height)
    print("Pipeline: BSP generation step (placeholder)")
    return context

def step_place_rooms(context: DungeonContext) -> DungeonContext:
    """Place rooms based on BSP leaves."""
    # Placeholder: would call RoomPlacer
    print("Pipeline: Room placement step (placeholder)")
    return context

def step_connect_rooms(context: DungeonContext) -> DungeonContext:
    """Connect rooms with corridors."""
    print("Pipeline: Room connection step (placeholder)")
    return context

def step_add_walls(context: DungeonContext) -> DungeonContext:
    """Add walls around floor tiles."""
    print("Pipeline: Wall generation step (placeholder)")
    return context
