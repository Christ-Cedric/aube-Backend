import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/subscription_db")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "subscription_db")

async def check_user():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    users_collection = db.users
    
    # Check for the user created in tests
    email_to_check = "debug_user_v3@example.com"
    user = await users_collection.find_one({"email": email_to_check})
    
    if user:
        print(f"SUCCESS: Found user {user['email']} in database.")
        print(f"User ID: {user['id']}")
    else:
        print(f"FAILURE: User {email_to_check} not found in database.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_user())
