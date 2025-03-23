import asyncio
import logging
from time import time

from motor.core import AgnosticDatabase

from core.settings import settings
from databases.base import RatePoint
from databases.mongo.base import rate_db

logger = logging.getLogger('app_logger')


class RateRepository:
    def __init__(self, db: AgnosticDatabase):
        self.collection = db.rates

    async def init_db(self):
        logger.info('Initializing DB')
        await self.collection.create_index({'assetId': 1, 'time': 1, 'assetName': 1, 'value': 1})

    async def get_assets_points(self, asset_id: int, period: int = settings.HISTORY_PERIOD) -> list[RatePoint]:
        cutoff_time = int(time()) - period
        cursor = self.collection.find(
            {'assetId': asset_id, 'time': {'$gte': cutoff_time}},
            projection={'_id': False, 'assetId': 1, 'time': 1, 'assetName': 1, 'value': 1},
        ).sort('time', 1)
        return await cursor.to_list()

    async def insert_many(self, points: list[RatePoint]):
        await self.collection.insert_many(points)


async def main():
    repository = RateRepository(rate_db)
    await repository.insert_many([{'symbol': ' GBPJPY', 'value': 162.495, 'asset_id': 1, 'time': 2}])


if __name__ == '__main__':
    asyncio.run(main())
