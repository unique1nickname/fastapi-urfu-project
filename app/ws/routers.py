from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.manager import manager

ws_router = APIRouter()

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.handle(data, websocket)
            if data == "close":
                break
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
