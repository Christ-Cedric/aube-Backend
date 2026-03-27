from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import db
from app.core.logging import setup_logging
from app.api.v1 import subscriptions, ads, websockets, auth, user
from app.tasks.expiration_checker import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    await db.connect_to_database()
    scheduler.start()
    yield
    # Shutdown
    await db.close_database_connection()
    scheduler.shutdown()

app = FastAPI(
    title="Mobile Client Backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subscriptions.router, prefix="/v1", tags=["Subscriptions"])
app.include_router(ads.router, prefix="/v1", tags=["Ads"])
app.include_router(websockets.router, tags=["WebSockets"])
app.include_router(auth.router, prefix="/v1", tags=["Authentication"])
app.include_router(user.router, prefix="/v1", tags=["User Profile"])

# Temporarily disabled - requires Redis
# from app.middleware.rate_limiter import RateLimitMiddleware
# app.add_middleware(RateLimitMiddleware)

from fastapi.staticfiles import StaticFiles
import os

from fastapi.responses import RedirectResponse

# Serve Web Client at /client to avoid shadowing API routes
web_client_path = os.path.join(os.path.dirname(__file__), "..", "web_client")
if os.path.exists(web_client_path):
    app.mount("/client", StaticFiles(directory=web_client_path, html=True), name="web_client")

@app.get("/")
async def root():
    return RedirectResponse(url="/client/index.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected" if db.client else "disconnected"}

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
