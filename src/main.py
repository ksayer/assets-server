import asyncio

import websockets

from core.logger import setup_logger
from databases.mongo.base import client, rate_db
from databases.mongo.repository import RateRepository
from services.parser import RatesParser
from services.rates_service import RateService
from services.server import WebsocketServer


async def main():
    try:
        setup_logger()
        service = RateService(repository=RateRepository(db=rate_db), parser=RatesParser())
        ws_server = websockets.serve(WebsocketServer(service), '0.0.0.0', 8080)
        await asyncio.gather(ws_server, service.start())
    finally:
        client.close()


if __name__ == '__main__':
    asyncio.run(main())
