import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)  # {identifier: [timestamps]}
        logger.info("Rate limiter initialized (in-memory mode)")

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        identifier = request.client.host if request.client else "unknown"
        limit = settings.RATE_LIMIT_PER_MINUTE
        window = 60  # seconds
        
        now = time.time()
        
        # Clean old requests outside the window
        self.requests[identifier] = [
            ts for ts in self.requests[identifier] 
            if ts > now - window
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )
        
        # Record this request
        self.requests[identifier].append(now)
        
        return await call_next(request)

