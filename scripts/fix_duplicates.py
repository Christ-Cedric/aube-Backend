import asyncio
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Charger l'environnement
load_dotenv()

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "admin_db") # Adaptez si nécessaire, ou vérifiez .env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_duplicates():
    logger.info(f"Connecting to MongoDB: {MONGODB_URI} (DB: {DATABASE_NAME})")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db["transactions"]
    
    # ---------------------------------------------------------
    # PARTIE 1 : Nettoyer les doublons LOGIQUES (Même transaction métier)
    # (user_id, numero_de_piece, date_de_transaction)
    # ---------------------------------------------------------
    pipeline = [
        {
            "$group": {
                "_id": {
                    "user_id": "$user_id",
                    "numero_de_piece": "$numero_de_piece",
                    "date_de_transaction": "$date_de_transaction"
                },
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"} # On collecte tous les _id
            }
        },
        {
            "$match": {
                "count": {"$gt": 1} # On ne garde que les groupes > 1
            }
        }
    ]
    
    logger.info("Scanning for LOGICAL duplicates (user + piece + date)...")
    cursor = collection.aggregate(pipeline)
    
    logical_dups_found = 0
    deleted_count = 0
    
    async for doc in cursor:
        logical_dups_found += 1
        ids = doc["ids"]
        # Stratégie : Garder le PREMIER inséré (ou dernier, peu importe, elles sont identiques métier)
        # Idéalement on garde celle qui a `is_synced=True` si mélange, mais ici on simplifie
        keep_id = ids[0]
        remove_ids = ids[1:]
        
        logger.info(f"Duplicate Group found: {doc['_id']} (Count: {doc['count']})")
        logger.info(f"Keeping: {keep_id}, Deleting: {len(remove_ids)} others")
        
        result = await collection.delete_many({"_id": {"$in": remove_ids}})
        deleted_count += result.deleted_count
        
    logger.info(f"Logical Scan Done. Found {logical_dups_found} groups. Deleted {deleted_count} docs.")

    # ---------------------------------------------------------
    # PARTIE 2 : Créer l'Index Unique LOGIQUE
    # ---------------------------------------------------------
    try:
        logger.info("Creating UNIQUE INDEX on (user_id, numero_de_piece, date_de_transaction)...")
        await collection.create_index(
            [("user_id", 1), ("numero_de_piece", 1), ("date_de_transaction", 1)],
            unique=True,
            name="unique_logical_transaction"
        )
        logger.info("✅ Logical Unique Index Created.")
    except Exception as e:
        logger.error(f"❌ Failed to create Logical Index: {e}")

    # ---------------------------------------------------------
    # PARTIE 3 : Créer l'Index Unique ID (Technique)
    # ---------------------------------------------------------
    # Note: On suppose que le nettoyage logique a aussi réglé les problèmes d'ID dupliqués
    # car généralement duplicate ID = duplicate transaction.
    # Mais par sécurité, on peut scanner les IDs aussi si nécessaire.
    
    try:
        logger.info("Creating UNIQUE INDEX on (id)...")
        # Si 'id' est un UUID stocké en String ou Binary
        await collection.create_index("id", unique=True, name="unique_transaction_id")
        logger.info("✅ ID Unique Index Created.")
    except Exception as e:
        logger.error(f"❌ Failed to create ID Index (Check for ID duplicates!): {e}")

    client.close()
    logger.info("Cleanup script finished.")

if __name__ == "__main__":
    asyncio.run(fix_duplicates())
