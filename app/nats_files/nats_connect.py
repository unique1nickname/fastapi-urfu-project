import nats, json
from ws.manager import manager

NATS_URL = "nats://0.0.0.0:4222"
CHANNEL_NAME = "items.updates"

nc: nats.NATS | None = None

async def connect():
    global nc
    if nc is None or nc.is_closed:
        nc = await nats.connect(NATS_URL)
    return nc

async def disconnect():
    global nc
    if nc is not None and not nc.is_closed:
        await nc.drain()
        await nc.close()
        nc = None

async def message_handler(msg):
        data = msg.data.decode()
        event_types = (
            "task_completed",
            "item_created",
            "item_updated",
            "item_deleted"
        )
        try:
            json_dict = json.loads(data)
            event_type = json_dict.get("event")
            if event_type not in event_types:
                await manager.broadcast(data)
        except json.decoder.JSONDecodeError:
            print(f"NATS msg: {data}")
            await manager.broadcast(f"NATS msg: {data}")