from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_to_database(self):
        logging.info("Connecting to MongoDB...")
        self.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            minPoolSize=10,
            maxPoolSize=50
        )
        self.db = self.client[settings.MONGODB_DATABASE]
        logging.info("Connected to MongoDB.")

    async def close_database_connection(self):
        logging.info("Closing MongoDB connection...")
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed.")

db = Database()

async def get_database():
    return db.db
