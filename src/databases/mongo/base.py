from motor.motor_asyncio import AsyncIOMotorClient

from core.settings import settings

client: AsyncIOMotorClient = AsyncIOMotorClient(settings.MONGO_URI)
rate_db = client.rate_db
