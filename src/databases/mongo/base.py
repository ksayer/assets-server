from motor.motor_asyncio import AsyncIOMotorClient

from core.settings import settings

mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(settings.MONGO_URI, timeoutms=3000)


async def get_rate_db():
    rate_db = mongo_client.rate_db
    await rate_db.rates.create_index({'assetId': 1, 'time': 1, 'assetName': 1, 'value': 1})
    return rate_db
