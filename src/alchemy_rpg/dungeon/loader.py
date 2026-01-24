import json
import os
from typing import Dict, Any, Optional
from .context import DungeonContext

class DungeonLoader:
    """
    讀取 flow.json 配置文件並指揮地牢生成。
    """
    def __init__(self, data_path: str = "data/dungeon_flows"):
        self.data_path = data_path
        self.flows: Dict[str, Dict] = {}
        
    def load_flow(self, flow_name: str) -> Optional[Dict[str, Any]]:
        """Load a dungeon flow configuration from JSON."""
        file_path = os.path.join(self.data_path, f"{flow_name}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.flows[flow_name] = json.load(f)
                return self.flows[flow_name]
        else:
            print(f"DungeonLoader: Flow file not found: {file_path}")
            return None
    
    def get_flow(self, flow_name: str) -> Optional[Dict[str, Any]]:
        """Get a previously loaded flow, or load it if not cached."""
        if flow_name in self.flows:
            return self.flows[flow_name]
        return self.load_flow(flow_name)
    
    def create_context_from_flow(self, flow_name: str) -> DungeonContext:
        """Create a DungeonContext based on a flow configuration."""
        flow = self.get_flow(flow_name)
        if not flow:
            print(f"DungeonLoader: Using default context for missing flow: {flow_name}")
            return DungeonContext()
        
        ctx = DungeonContext(
            grid_width=flow.get('grid_width', 100),
            grid_height=flow.get('grid_height', 80),
            tile_size=flow.get('tile_size', 32),
            dungeon_id=flow.get('dungeon_id', 0),
            seed=flow.get('seed', None)
        )
        ctx.reset()
        return ctx
