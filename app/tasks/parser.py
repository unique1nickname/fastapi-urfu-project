from db import models
from db.db import get_db
from ws.manager import manager
from nats_files import nats_connect
from playwright.async_api import async_playwright
import datetime, asyncio, json

URL = "https://www.cbr.ru/eng/currency_base/daily/"

# Добавить сохранение в БД
async def run_parser(url: str):
    parser = CBRCurrencyParser()
    await parser.start()
    await parser.load_page(url)
    currencies_data = await parser.parce_currency()
    await parser.browser.close()
    db_gen = get_db()
    db = await anext(db_gen)
    try:
        db.add_all(currencies_data)
        await db.commit()
        for data in currencies_data:
            await db.refresh(data)
    finally:
        await db_gen.aclose()
    
    # ws and nats
    currencies_data_dict = list()
    for i in currencies_data:
        i.date = str(i.date)
        currencies_data_dict.append(i.model_dump())
    
    json_dump = json.dumps({
        "event": "task_completed",
        "data": currencies_data_dict
    })
    await manager.broadcast(json_dump)
    nc = await nats_connect.connect()
    await nc.publish(nats_connect.CHANNEL_NAME, json_dump.encode())

    print(f"Найдено:\n{currencies_data}")
    return


async def background_task():
    while True:
        await run_parser(URL)
        await asyncio.sleep(300)


class CBRCurrencyParser:
    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        context = await self.browser.new_context()
        self.page = await context.new_page()

    async def load_page(self, url):
        await self.page.goto(url)
        await self.page.wait_for_selector('.data', timeout=15_000)

    async def parce_currency(self) -> list[models.CurrencyCreate]:
        currencies = list()
        
        date_el = await self.page.query_selector('.datepicker-filter_button')
        date = await date_el.inner_text()
        date = datetime.datetime.strptime(date, "%d.%m.%Y").date()

        items = await self.page.query_selector('.data')
        items = await items.query_selector_all('tr')

        for item in items[1:]:
            currency_data = list()
            
            item_el = await item.query_selector_all('td')
            for td_el in item_el:
                text = await td_el.inner_text()
                currency_data.append(text)
            
            currency_model = models.CurrencyModel(
                name=currency_data[3],
                unit=int(currency_data[2]),
                char_code=currency_data[1],
                num_code=int(currency_data[0]),
                rate=float(currency_data[4]),
                date=date
            )
            currencies.append(currency_model)

        return currencies  