from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connection: list[WebSocket] = list()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connection.append(websocket)

    async def handle(self, data: str, websocket: WebSocket):
        if data == "spec":
            await websocket.send_text("SPEC OK!")
        elif data == "close":
            await self.disconnect(websocket)
        else:
            await websocket.send_text(f"Your data: {data}")

    async def disconnect(self, websocket: WebSocket):
        await websocket.close()
        self.active_connection.remove(websocket)

    async def broadcast(self, data: str):
        for ws in self.active_connection:
            await ws.send_text(data)

manager = ConnectionManager()