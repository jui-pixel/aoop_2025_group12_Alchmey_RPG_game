from typing import Tuple
from .dungeon.dungeon import Dungeon
from .dungeon.room import Room
from .config import TILE_SIZE

class DungeonManager:
    def __init__(self, game: 'Game'):
        self.game = game
        self.dungeon = Dungeon()
        self.dungeon.game = game
        self.current_room_id = 0

    def initialize_lobby(self) -> None:
        """Initialize the lobby room."""
        self.dungeon.initialize_lobby()
        self.current_room_id = 0

    def get_current_room(self) -> Room:
        """Get the current room."""
        return self.dungeon.rooms[self.current_room_id]

    def get_room_center(self, room: Room) -> Tuple[float, float]:
        """Calculate the center of a room."""
        return (
            (room.x + room.width / 2) * TILE_SIZE,
            (room.y + room.height / 2) * TILE_SIZE
        )

    def switch_room(self, new_room_id: int) -> bool:
        """Switch to a new room if valid."""
        if 0 <= new_room_id < len(self.dungeon.rooms):
            self.current_room_id = new_room_id
            return True
        return False

    def get_dungeon(self) -> Dungeon:
        """Get the dungeon instance."""
        return self.dungeon