import pytest
import uuid
from httpx import AsyncClient, ASGIjosue_appport
from app.main import app
from app.core.database import db


@pytest.mark.asyncio
async def test_complete_profile_and_device_flow():
    """Test the complete user profile and device management flow."""
    
    # Setup database
    await db.connect_to_database()
    
    try:
        # Generate unique email for this test run
        test_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "SecurePass123"
        
        async with AsyncClient(josue_appport=ASGIjosue_appport(app=app), base_url="http://test") as ac:
            
            # Step 1: Signup
            signup_response = await ac.post("/v1/auth/signup", json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test User"
            })
            assert signup_response.status_code == 201, f"Signup failed: {signup_response.text}"
            user_data = signup_response.json()
            assert user_data["email"] == test_email
            
            # Step 2: Login
            login_response = await ac.post("/v1/auth/login", json={
                "email": test_email,
                "password": test_password
            })
            assert login_response.status_code == 200, f"Login failed: {login_response.text}"
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Step 3: Get Profile
            profile_response = await ac.get("/v1/user/profile", headers=headers)
            assert profile_response.status_code == 200, f"Get profile failed: {profile_response.text}"
            profile = profile_response.json()
            assert profile["email"] == test_email
            
            # Step 4: Update Profile
            update_response = await ac.patch("/v1/user/profile", headers=headers, json={
                "full_name": "Updated Test User",
                "phone_number": "+1234567890"
            })
            assert update_response.status_code == 200, f"Update failed: {update_response.text}"
            updated_profile = update_response.json()
            assert updated_profile["full_name"] == "Updated Test User"
            assert updated_profile["phone_number"] == "+1234567890"
            
            # Step 5: Add Device
            device_id = str(uuid.uuid4())
            device_response = await ac.post("/v1/user/devices", headers=headers, json={
                "device_id": device_id,
                "device_name": "iPhone 14 Pro",
                "os_type": "iOS",
                "fcm_token": "fcm_token_123",
                "is_primary": True
            })
            assert device_response.status_code == 200, f"Add device failed: {device_response.text}"
            
            # Step 6: List Devices
            list_response = await ac.get("/v1/user/devices", headers=headers)
            assert list_response.status_code == 200, f"List devices failed: {list_response.text}"
            devices = list_response.json()
            assert len(devices) == 1
            assert devices[0]["device_id"] == device_id
            
            # Step 7: Remove Device
            delete_response = await ac.delete(f"/v1/user/devices/{device_id}", headers=headers)
            assert delete_response.status_code == 204, f"Delete failed: {delete_response.status_code}"
            
            # Step 8: Verify Empty List
            final_list_response = await ac.get("/v1/user/devices", headers=headers)
            assert final_list_response.status_code == 200
            final_devices = final_list_response.json()
            assert len(final_devices) == 0
            
    finally:
        await db.close_database_connection()


@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test that endpoints require authentication."""
    
    await db.connect_to_database()
    
    try:
        async with AsyncClient(josue_appport=ASGIjosue_appport(app=app), base_url="http://test") as ac:
            # Try to access profile without token
            profile_res = await ac.get("/v1/user/profile")
            assert profile_res.status_code == 401
            
            # Try to list devices without token
            devices_res = await ac.get("/v1/user/devices")
            assert devices_res.status_code == 401
    finally:
        await db.close_database_connection()
