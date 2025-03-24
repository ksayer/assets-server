import json
import logging
from time import time
from redis.asyncio import Redis

from core.settings import settings
from databases.base import RatePoint

logger = logging.getLogger('app_logger')


class RateRepositoryRedis:
    def __init__(self, db: Redis):
        self._redis = db

    async def get_assets_points(self, asset_id: int, period: int = settings.HISTORY_PERIOD) -> list[RatePoint]:
        cutoff_time = int(time()) - period
        key = f"rate:{asset_id}"
        raw_items = await self._redis.lrange(key, 0, -1) # type: ignore

        points = []
        for item in raw_items:
            data = json.loads(item)
            points.append(data)
        points = [p for p in points if p["time"] >= cutoff_time]
        return points

    async def insert_many(self, points: list[RatePoint]) -> None:
        if not points:
            return

        pipe = self._redis.pipeline()

        for p in points:
            key = f"rate:{p['assetId']}"
            json_value = json.dumps(p)
            pipe.rpush(key, json_value)
            pipe.ltrim(key, -settings.HISTORY_PERIOD, -1)

        await pipe.execute()
