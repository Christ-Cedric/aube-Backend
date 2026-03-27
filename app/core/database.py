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
        
        # Créer les index après la connexion
        await self.create_indexes()

    async def create_indexes(self):
        """Crée les index nécessaires dans MongoDB"""
        try:
            logging.info("Creating database indexes...")
            
            # Index unique sur phone_number
            await self.db["users"].create_index("phone_number", unique=True)
            logging.info("✅ Created unique index on phone_number")
            
            # Index unique partiel sur email (seulement si non null)
            await self.db["users"].create_index(
                "email", 
                unique=True, 
                partialFilterExpression={"email": {"$type": "string"}}
            )
            logging.info("✅ Created partial unique index on email")
            
            # Index sur created_at pour tri
            await self.db["users"].create_index("created_at")
            logging.info("✅ Created index on created_at")
            
            # Index sur is_active pour filtrage
            await self.db["users"].create_index("is_active")
            logging.info("✅ Created index on is_active")
            
            # Index pour les sessions utilisateur
            await self.db["user_sessions"].create_index("user_id")
            await self.db["user_sessions"].create_index("refresh_token_hash")
            await self.db["user_sessions"].create_index("expires_at")
            logging.info("✅ Created indexes on user_sessions")
            
            # Index pour les devices
            await self.db["user_devices"].create_index([("user_id", 1), ("device_id", 1)], unique=True)
            await self.db["user_devices"].create_index("user_id")
            logging.info("✅ Created indexes on user_devices")
            
            # Ajoutez ceci dans la méthode create_indexes() de app/core/database.py

            # Index pour les transactions
            await self.db["transactions"].create_index("user_id")
            await self.db["transactions"].create_index([("user_id", 1), ("date_de_transaction", -1)])
            await self.db["transactions"].create_index("type_de_transaction")
            await self.db["transactions"].create_index("operateur")
            await self.db["transactions"].create_index("date_de_transaction")
            logging.info("✅ Created indexes on transactions")

            logging.info("✅ All database indexes created successfully")
            
        except Exception as e:
            logging.error(f"❌ Error creating indexes: {e}")
            # On ne lève pas d'exception pour ne pas bloquer le démarrage
            # Les index manquants causeront simplement des performances réduites

    async def close_database_connection(self):
        logging.info("Closing MongoDB connection...")
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed.")

db = Database()

async def get_database():
    return db.db