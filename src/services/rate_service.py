import logging
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

from core.settings import settings
from databases.base import RatePoint, RateRepositoryProtocol
from services.parser import RatesParser
from services.worker_pool import AsyncWorkerPool

logger = logging.getLogger('app_logger')

SYMBOL_MAP_ID = {s['name']: s['id'] for s in settings.AVAILABLE_SYMBOLS}
SYMBOLS_IDS = [s['id'] for s in settings.AVAILABLE_SYMBOLS]
SubscriberId = str


@dataclass
class Subscriber:
    callback: Callable[[RatePoint], Awaitable[None]]
    asset_id: int


class RateService:
    """
    Service that manages currency rate updates:
    - receives real-time rate data,
    - stores it in the database
    - notifies active subscribers
    """

    def __init__(
        self,
        repository: RateRepositoryProtocol,
        parser: RatesParser,
        notifier_worker_pool: AsyncWorkerPool,
        db_worker_pool: AsyncWorkerPool,
    ):
        self.repository = repository
        self.parser = parser
        self.notifier_pool = notifier_worker_pool
        self.db_worker_pool = db_worker_pool
        self.subscribers: dict[SubscriberId, Subscriber] = {}

    async def start(self):
        async for rates in self.parser.stream_rates():
            points, timestamp = [], int(time.time())
            for rate in rates:
                if rate['Symbol'] in SYMBOL_MAP_ID:
                    value = (rate['Ask'] + rate['Bid']) / 2
                    point = RatePoint(
                        assetId=SYMBOL_MAP_ID[rate['Symbol']],
                        assetName=rate['Symbol'],
                        time=timestamp,
                        value=value,
                    )
                    points.append(point.copy())
                    self._notify_subscribers(point)
            if points:
                logger.debug(f'Save new points: {points=}')
                self.db_worker_pool.submit(self.repository.insert_many, points)

    def subscribe(self, subscriber_id: str, callback: Callable[[RatePoint], Awaitable[None]], asset_id: int):
        self.unsubscribe(subscriber_id)
        if self._asset_id_is_available(asset_id):
            self.subscribers[subscriber_id] = Subscriber(callback, asset_id)
            logger.info(f'New subscriber: {subscriber_id}')

    def unsubscribe(self, subscriber_id: str):
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.info(f'Unsubscribe: {subscriber_id}')

    async def get_history(self, asset_id: int) -> list[RatePoint]:
        return await self.repository.get_assets_points(asset_id=asset_id)

    def _notify_subscribers(self, point: RatePoint):
        for subscriber_id, subscriber in self.subscribers.items():
            try:
                if point['assetId'] == subscriber.asset_id:
                    self.notifier_pool.submit(subscriber.callback, point)
            except Exception as e:
                logger.error(f'Error while notify subscriber {subscriber_id}: {e}')

    @staticmethod
    def get_symbols() -> list[dict[str, int | str]]:
        return settings.AVAILABLE_SYMBOLS

    @staticmethod
    def _asset_id_is_available(asset_id: int):
        return asset_id in SYMBOLS_IDS

