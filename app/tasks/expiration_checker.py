from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import db
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

async def check_expired_subscriptions():
    logger.info("Running expiration check...")
    if db.db is None:
        logger.warning("Database not connected, skipping expiration check")
        return

    now = datetime.now(timezone.utc)
    collection = db.db.subscriptions
    
    result = await collection.update_many(
        {
            "status": "validated",
            "expires_at": {"$lt": now}
        },
        {"$set": {"status": "expired"}}
    )
    
    if result.modified_count > 0:
        logger.info(f"Expired {result.modified_count} subscriptions.")
    else:
        logger.info("No subscriptions expired.")

scheduler = AsyncIOScheduler()
scheduler.add_job(check_expired_subscriptions, 'interval', hours=1)
