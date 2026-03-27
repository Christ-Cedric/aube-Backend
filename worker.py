import asyncio
import logging
from app.tasks.expiration_checker import check_expired_subscriptions
from app.core.database import db
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)

async def main():
    setup_logging()
    await db.connect_to_database()
    logger.info("Worker started.")
    
    try:
        while True:
            await check_expired_subscriptions()
            # Run every hour
            await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
    finally:
        await db.close_database_connection()
        logger.info("Worker stopped.")

if __name__ == "__main__":
    asyncio.run(main())
