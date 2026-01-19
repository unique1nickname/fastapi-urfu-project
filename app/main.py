from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import SQLModel

import time, asyncio

from api.routers import api_router
from ws.routers import ws_router
from ws.manager import manager
from db.db import engine
from tasks.parser import background_task
from nats_files import nats_connect

import nats, json


app = FastAPI(
    title="My project",
    version="1.0"
)

app.include_router(api_router)
app.include_router(ws_router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(
            SQLModel.metadata.create_all
        )
    
    asyncio.create_task(background_task())

    nc = await nats_connect.connect()
    await nc.subscribe(
        nats_connect.CHANNEL_NAME,
        cb=nats_connect.message_handler
    )

@app.on_event("shutdown")  # Аналог для drain
async def on_shutdown():
    nats_connect.disconnect()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def log_request(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"Request to {request.url.path} processed in {process_time:.4f} seconds")
    return response