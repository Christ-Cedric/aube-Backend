import asyncio
import sys
import os
sys.path.append(os.getcwd())

from httpx import AsyncClient, ASGIjosue_appport
from app.main import app

from app.core.database import db

async def main():
    await db.connect_to_database()
    try:
        async with AsyncClient(josue_appport=ASGIjosue_appport(app=app), base_url="http://test") as ac:
            print("Sending signup request...")
            try:
                response = await ac.post("/v1/auth/signup", json={
                    "email": "debug_user_v3@example.com",
                    "password": "password123",
                    "full_name": "Debug User"
                })
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
            except Exception as e:
                print(f"Signup failed: {e}")

            print("Sending login request...")
            try:
                response = await ac.post("/v1/auth/login", json={
                    "email": "debug_user_v3@example.com",
                    "password": "password123"
                })
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
            except Exception as e:
                print(f"Login failed: {e}")
    finally:
        await db.close_database_connection()

if __name__ == "__main__":
    asyncio.run(main())
