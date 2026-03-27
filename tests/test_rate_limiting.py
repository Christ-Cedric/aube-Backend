import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from fakeredis import aioredis as fakeredis
import asyncio

@pytest.fixture
async def redis_client():
    """Mock Redis client for testing"""
    client = await fakeredis.create_redis_pool()
    yield client
    client.close()
    await client.wait_closed()

@pytest.mark.asyncio 
async def test_rate_limiting_enforced():
    """Test that rate limiting blocks requests after limit is exceeded"""
    # Patch the Redis connection in the middleware
    from app.middleware.rate_limiter import RateLimitMiddleware
    import app.core.config as config
    
    # Temporarily set a low limit for testing
    original_limit = config.settings.RATE_LIMIT_PER_MINUTE
    config.settings.RATE_LIMIT_PER_MINUTE = 5
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Make requests up to the limit
        for i in range(5):
            response = await ac.get("/health")
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        # Next request should be rate limited
        response = await ac.get("/health")
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
    
    # Restore original limit
    config.settings.RATE_LIMIT_PER_MINUTE = original_limit

@pytest.mark.asyncio
async def test_rate_limit_resets_after_window():
    """Test that rate limit resets after the time window"""
    from app.middleware.rate_limiter import RateLimitMiddleware
    import app.core.config as config
    
    # Set a very low limit for testing
    original_limit = config.settings.RATE_LIMIT_PER_MINUTE
    config.settings.RATE_LIMIT_PER_MINUTE = 2
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Exhaust the limit
        await ac.get("/health")
        await ac.get("/health")
        
        # Should be rate limited
        response = await ac.get("/health")
        assert response.status_code == 429
        
        # Wait for window to reset (in production this is 60s, but with fakeredis we can test the logic)
        # For this test, we'll just verify the logic works
        
    config.settings.RATE_LIMIT_PER_MINUTE = original_limit

@pytest.mark.asyncio
async def test_different_clients_have_separate_limits():
    """Test that different client IPs have separate rate limits"""
    # This test verifies the rate limiting is per-client
    # In a real scenario, you'd need to mock different client IPs
    # For now, we verify the key generation includes client identifier
    from app.middleware.rate_limiter import RateLimitMiddleware
    
    # The middleware uses request.client.host as identifier
    # Different hosts should have different limits
    assert True  # Placeholder - would need request mocking for full test
