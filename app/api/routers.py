from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.exceptions import HTTPException

from sqlalchemy import Select

from db import models
from db.db import DBSession, get_db

from ws.manager import manager

from nats_files import nats_connect

from tasks import parser

import json

api_router = APIRouter()



@api_router.get("/items", response_model=list[models.CurrencyModel])
async def get_items(db: DBSession = Depends(get_db)):
    data = Select(models.CurrencyModel)
    result = await db.execute(data)
    return result.scalars()

@api_router.get("/items/{item_id}", response_model=models.CurrencyModel)
async def get_item(item_id: int, db: DBSession = Depends(get_db)):
    obj = await db.get(models.CurrencyModel, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    return obj

@api_router.post("/items", response_model=models.CurrencyModel, status_code=201)
async def create_item(item: models.CurrencyCreate, db: DBSession = Depends(get_db)):
    new_item = models.CurrencyModel(
        name=item.name,
        unit=item.unit,
        char_code=item.char_code,
        num_code=item.num_code, 
        rate=item.rate,
        date=item.date
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    # ws broadcast
    new_item.date = str(new_item.date)
    json_str = new_item.model_dump()
    json_dump = json.dumps({
        "event": "item_created",
        "data": json_str
    })
    await manager.broadcast(json_dump)
    nc = await nats_connect.connect()
    await nc.publish(nats_connect.CHANNEL_NAME, json_dump.encode())

    return new_item

@api_router.patch("/items/{item_id}", response_model=models.CurrencyModel)
async def update_item(item_id: int, item_update: models.CurrencyUpdate, db: DBSession = Depends(get_db)):
    obj = await db.get(models.CurrencyModel, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(obj, field, value)

    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    # ws broadcast
    obj.date = str(obj.date)
    json_str = obj.model_dump()
    json_dump = json.dumps({
        "event": "item_updated",
        "data": json_str
    })
    await manager.broadcast(json_dump)
    nc = await nats_connect.connect()
    await nc.publish(nats_connect.CHANNEL_NAME, json_dump.encode())

    return obj

@api_router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int, db: DBSession = Depends(get_db)):
    obj = await db.get(models.CurrencyModel, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(obj)
    await db.commit()

    # ws broadcast
    json_dump = json.dumps({
        "event": "item_deleted",
        "data": {"id": item_id}
    })
    await manager.broadcast(json_dump)
    nc = await nats_connect.connect()
    await nc.publish(nats_connect.CHANNEL_NAME, json_dump.encode())
    
    return
 

@api_router.post("/tasks/run", status_code=201)
async def run_task(background_task: BackgroundTasks, db: DBSession = Depends(get_db)):
    # force run task
    background_task.add_task(parser.run_parser, parser.URL)
    return {"message": "Парсер запущен в фоне"}