import asyncio
import logging
import time
from typing import Awaitable, Callable

from core.settings import settings
from databases.mongo.base import rate_db
from databases.mongo.repository import RatePoint, RateRepository
from services.parser import RatesParser

logger = logging.getLogger('app_logger')

SYMBOL_MAP_ID = {s['name']: s['id'] for s in settings.AVAILABLE_SYMBOLS}
SYMBOLS_IDS = [s['id'] for s in settings.AVAILABLE_SYMBOLS]


class RateService:
    def __init__(self, repository: RateRepository, parser: RatesParser):
        self.repository = repository
        self.parser = parser
        self.subscribers: dict[str, Callable[[RatePoint], Awaitable[None]]] = {}

    async def start(self):
        async for rates in self.parser.stream_rates():
            points = []
            for rate in rates:
                if rate['Symbol'] in SYMBOL_MAP_ID:
                    value = (rate['Ask'] + rate['Bid']) / 2
                    point = RatePoint(
                        assetId=SYMBOL_MAP_ID[rate['Symbol']], symbol=rate['Symbol'], time=int(time.time()), value=value
                    )
                    points.append(point)
                    await self._notify_subscribers(point)
            if points:
                logger.debug(f'Save new points: {points=}')
                await self.repository.insert_many(points)

    def subscribe(self, subscriber_id: str, callback: Callable[[RatePoint], Awaitable[None]]):
        self.unsubscribe(subscriber_id)
        self.subscribers[subscriber_id] = callback
        logger.info(f'New subscriber: {subscriber_id}')

    def unsubscribe(self, subscriber_id: str):
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.info(f'Unsubscribe: {subscriber_id}')

    async def get_history(self, asset_id: int) -> list[RatePoint]:
        return await self.repository.get_all_by_period(asset_id=asset_id)

    async def _notify_subscribers(self, point: RatePoint):
        for subscriber_id, callback in self.subscribers.items():
            try:
                await callback(point)
            except Exception as e:
                logger.error(f'Error while notify subscriber {subscriber_id}: {e}')

    @staticmethod
    def get_symbols() -> list[dict[str, int | str]]:
        return settings.AVAILABLE_SYMBOLS

    @staticmethod
    def asset_id_is_available(asset_id: int):
        return asset_id in SYMBOLS_IDS


async def main():
    service = RateService(repository=RateRepository(db=rate_db), parser=RatesParser())
    logger.info(await service.get_history(2))


if __name__ == '__main__':
    asyncio.run(main())
