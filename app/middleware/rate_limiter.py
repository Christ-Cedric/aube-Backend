from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis.asyncio as redis
from app.core.config import settings
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        # Determine identifier (IP or user ID if authenticated)
        # For simplicity, using client IP. In production, consider X-Forwarded-For behind proxy.
        identifier = request.client.host
        
        # Consider making rate limit configurable per endpoint or user role
        key = f"rate_limit:app:{identifier}"
        limit = settings.RATE_LIMIT_PER_MINUTE
        
        # Check current usage
        current = await self.redis.get(key)
        if current and int(current) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
            
        # Increment usage
        pipe = self.redis.pipeline()
        pipe.incr(key)
        if not current:
            # Set expiry for first request in window
            pipe.expire(key, 60)
        await pipe.execute()
        
        return await call_next(request)
