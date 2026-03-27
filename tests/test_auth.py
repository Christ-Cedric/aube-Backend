import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import db

@pytest.fixture(autouse=True)
async def clear_db():
    await db.connect_to_database()
    await db.client["subscription_db"]["users"].delete_many({})
    yield
    await db.close_database_connection()

@pytest.mark.asyncio
async def test_signup_successful():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_signup_duplicate_email():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        await ac.post("/v1/auth/signup", json=payload)
        response = await ac.post("/v1/auth/signup", json=payload)
    
    assert response.status_code == 409
    assert response.json()["detail"] == "User with this email already exists"

@pytest.mark.asyncio
async def test_login_successful():
    # First signup
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/v1/auth/signup", json={
            "email": "login@example.com",
            "password": "password123"
        })
        
        # Then login
        response = await ac.post("/v1/auth/login", json={
            "email": "login@example.com",
            "password": "password123"
        })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
    
    assert response.status_code == 401
