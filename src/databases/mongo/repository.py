import asyncio
from time import time
from typing import TypedDict

from motor.core import AgnosticDatabase

from core.settings import settings
from databases.mongo.base import rate_db


class RatePoint(TypedDict):
    assetId: int
    symbol: str
    time: int
    value: float


class RateRepository:
    def __init__(self, db: AgnosticDatabase):
        self.collection = db.rates
        self.collection.create_index({'assetId': 1, 'time': 1, 'symbol': 1, 'value': 1})

    async def get_all_by_period(self, asset_id: int, period: int = settings.HISTORY_PERIOD) -> list[RatePoint]:
        cutoff_time = int(time()) - period
        cursor = self.collection.find(
            {'assetId': asset_id, 'time': {'$gte': cutoff_time}},
            projection={'_id': False, 'assetId': 1, 'time': 1, 'symbol': 1, 'value': 1},
        ).sort('time', 1)
        return await cursor.to_list()

    async def insert_many(self, points: list[RatePoint]) -> list[RatePoint]:
        await self.collection.insert_many(points)
        return points


async def main():
    repository = RateRepository(rate_db)
    await repository.insert_many([{'symbol': ' GBPJPY', 'value': 162.495, 'asset_id': 1, 'time': 2}])


if __name__ == '__main__':
    asyncio.run(main())
