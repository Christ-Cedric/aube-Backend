
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import uuid

# Use the same setup/teardown as test_auth or define here
# For simplicity, we assume the database is clean or we handle conflicts

@pytest.mark.asyncio
async def test_user_profile_flow():
    email = f"profile_test_{uuid.uuid4()}@example.com"
    password = "password123"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Signup
        signup_res = await ac.post("/v1/auth/signup", json={
            "email": email,
            "password": password,
            "full_name": "Profile User"
        })
        assert signup_res.status_code == 201
        
        # 2. Login
        login_res = await ac.post("/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Get Profile
        profile_res = await ac.get("/v1/user/profile", headers=headers)
        assert profile_res.status_code == 200
        profile_data = profile_res.json()
        assert profile_data["email"] == email
        assert profile_data["full_name"] == "Profile User"
        
        # 4. Update Profile
        update_res = await ac.patch("/v1/user/profile", headers=headers, json={
            "full_name": "Updated Name",
            "phone_number": "+1234567890"
        })
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["full_name"] == "Updated Name"
        assert updated_data["phone_number"] == "+1234567890"
        
        # 5. Add Device
        device_id = str(uuid.uuid4())
        device_res = await ac.post("/v1/user/devices", headers=headers, json={
            "device_id": device_id,
            "device_name": "Test Phone",
            "os_type": "Android",
            "fcm_token": "token123",
            "is_primary": True
        })
        assert device_res.status_code == 200
        
        # 6. List Devices
        list_res = await ac.get("/v1/user/devices", headers=headers)
        assert list_res.status_code == 200
        devices = list_res.json()
        assert len(devices) == 1
        assert devices[0]["device_id"] == device_id
        
        # 7. Remove Device
        del_res = await ac.delete(f"/v1/user/devices/{device_id}", headers=headers)
        assert del_res.status_code == 204
        
        # Verify empty
        list_res_empty = await ac.get("/v1/user/devices", headers=headers)
        devices_empty = list_res_empty.json()
        assert len(devices_empty) == 0
