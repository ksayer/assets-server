from redis.asyncio import Redis

from core.settings import settings

redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
