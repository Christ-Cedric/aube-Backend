import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import db
from app.core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    await db.connect_to_database()
    yield
    await db.close_database_connection()

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
