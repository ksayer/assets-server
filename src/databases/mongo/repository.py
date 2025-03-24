import logging
from time import time

from motor.core import AgnosticDatabase

from core.settings import settings
from databases.base import RatePoint

logger = logging.getLogger('app_logger')


class RateRepositoryMongo:
    def __init__(self, db: AgnosticDatabase):
        self.collection = db.rates

    async def get_assets_points(self, asset_id: int, period: int = settings.HISTORY_PERIOD) -> list[RatePoint]:
        cutoff_time = int(time()) - period
        cursor = self.collection.find(
            {'assetId': asset_id, 'time': {'$gte': cutoff_time}},
            projection={'_id': False, 'assetId': 1, 'time': 1, 'assetName': 1, 'value': 1},
        ).sort('time', 1)
        return await cursor.to_list()

    async def insert_many(self, points: list[RatePoint]):
        await self.collection.insert_many(points)
