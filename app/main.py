from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import db
from app.core.logging import setup_logging
from app.api.v1 import subscriptions, ads, websockets, auth, user
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    await db.connect_to_database()
    yield
    # Shutdown
    await db.close_database_connection()


app = FastAPI(
    title="Mobile Client Backend",
    version="1.0.0",
    lifespan=lifespan
)

from app.middleware.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")] if settings.CORS_ORIGINS else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(subscriptions.router, prefix="/v1", tags=["Subscriptions"])
app.include_router(ads.router, prefix="/v1", tags=["Ads"])
app.include_router(websockets.router, tags=["WebSockets"])
app.include_router(auth.router, prefix="/v1", tags=["Authentication"])
app.include_router(user.router, prefix="/v1", tags=["User Profile"])
from app.api.v1 import subscriptions, ads, websockets, auth, user, transactions
app.include_router(transactions.router, prefix="/v1", tags=["Transactions"])



@app.get("/")
async def root():
    return {"message": "Mobile Client Backend API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    health = {"status": "ok", "database": "disconnected"}
    
    # Check MongoDB
    if db.client:
        try:
            await db.client.admin.command('ping')
            health["database"] = "connected"
        except Exception:
            health["status"] = "unhealthy"
            
    return health



@app.get("/debug_routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": getattr(route, "path", str(route)),
            "name": getattr(route, "name", "None"),
            "methods": list(getattr(route, "methods", []))
        })
    return routes
