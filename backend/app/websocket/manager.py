from typing import Dict, Set
from fastapi import WebSocket
import uuid

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[uuid.UUID, Set[WebSocket]] = {}

    async def connect(self, game_id: uuid.UUID, websocket: WebSocket):
        # We assume the connection has already been accepted in the route endpoint
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)

    def disconnect(self, game_id: uuid.UUID, websocket: WebSocket):
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:  # Clean up empty sets
                del self.active_connections[game_id]

    async def broadcast(self, game_id: uuid.UUID, message: dict):
        if game_id in self.active_connections:
            # Iterate over a copy to avoid RuntimeError when removing from the set
            for connection in list(self.active_connections[game_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    self.disconnect(game_id, connection)
                    print(f"Error sending message to connection: {e}")

# Create a singleton instance to be imported across the application
manager = ConnectionManager()

manager = ConnectionManager()