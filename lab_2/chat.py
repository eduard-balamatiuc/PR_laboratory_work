from fastapi import WebSocket
from typing import Dict, Set
import asyncio


class ChatRoom:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def join_room(
        self,
        room_id: str,
        websocket: WebSocket,
    ):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)

    def remove_client(
        self,
        room_id: str,
        websocket: WebSocket,
    ):
        self.rooms[room_id].remove(websocket)
        if not self.rooms[room_id]:
            del self.rooms[room_id]

    async def broadcast_message(
        self,
        room_id: str,
        message: str,
        sender: WebSocket,
    ):
        if room_id in self.rooms:
            for client in self.rooms[room_id]:
                if client != sender:
                    await client.send_text(message)