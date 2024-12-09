from fastapi import WebSocket
from typing import Dict, Set, List
import asyncio


class ChatRoom:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.message_history: Dict[str, List[str]] = {}

    async def join_room(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
            self.message_history[room_id] = []
        self.rooms[room_id].add(websocket)
        
        for message in self.message_history[room_id]:
            await websocket.send_text(message)

    def remove_client(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
                del self.message_history[room_id]

    async def broadcast_message(self, room_id: str, message: str, sender: WebSocket):
        if room_id in self.rooms:
            self.message_history[room_id].append(message)
            self.message_history[room_id] = self.message_history[room_id][-50:]
            
            for client in self.rooms[room_id]:
                if client != sender:
                    await client.send_text(message)