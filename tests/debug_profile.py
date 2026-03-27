import asyncio
import sys
import os
import uuid
sys.path.append(os.getcwd())

from httpx import AsyncClient, ASGIjosue_appport
from app.main import app
from app.core.database import db

output_file = open("debug_profile_output.txt", "w", encoding="utf-8")

def log(msg):
    print(msg)
    output_file.write(msg + "\n")
    output_file.flush()

async def main():
    await db.connect_to_database()
    try:
        async with AsyncClient(josue_appport=ASGIjosue_appport(app=app), base_url="http://test") as ac:
            email = "debug_user_v3@example.com"
            password = "password123"
            
            log(f"Logging in as {email}...")
            login_res = await ac.post("/v1/auth/login", json={
                "email": email,
                "password": password
            })
            if login_res.status_code != 200:
                log(f"Login failed: {login_res.status_code} {login_res.text}")
                return
            
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            log("Login successful.")
            
            # Get Profile
            log("\nGetting profile from /v1/user/profile...")
            res = await ac.get("/v1/user/profile", headers=headers)
            log(f"Status: {res.status_code}")
            log(f"Response: {res.text}")

            # Update Profile
            log("\nUpdating profile...")
            res = await ac.patch("/v1/user/profile", headers=headers, json={
                "full_name": "Updated Debug User",
                "phone_number": "+15550000"
            })
            log(f"Status: {res.status_code}")
            log(f"Response: {res.text}")
            
            # Add Device
            device_id = str(uuid.uuid4())
            log(f"\nAdding device {device_id}...")
            res = await ac.post("/v1/user/devices", headers=headers, json={
                "device_id": device_id,
                "device_name": "Debug Phone",
                "os_type": "iOS",
                "is_primary": True
            })
            log(f"Status: {res.status_code}")
            log(f"Response: {res.text}")
            
            # List Devices
            log("\nListing devices...")
            res = await ac.get("/v1/user/devices", headers=headers)
            log(f"Status: {res.status_code}")
            log(f"Response: {res.text}")
            
            # Remove Device
            log(f"\nRemoving device {device_id}...")
            res = await ac.delete(f"/v1/user/devices/{device_id}", headers=headers)
            log(f"Status: {res.status_code}")

            # List Devices again
            log("\nListing devices after removal...")
            res = await ac.get("/v1/user/devices", headers=headers)
            log(f"Status: {res.status_code}")
            log(f"Response: {res.text}")
            
    except Exception as e:
        log(f"Error: {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        await db.close_database_connection()
        output_file.close()

if __name__ == "__main__":
    asyncio.run(main())
