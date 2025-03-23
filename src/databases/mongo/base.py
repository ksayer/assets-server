from motor.motor_asyncio import AsyncIOMotorClient

client: AsyncIOMotorClient = AsyncIOMotorClient('mongodb://root:utjvnrh36an112jsdm3hs632nsh3@localhost:27017')
rate_db = client.rate_db
