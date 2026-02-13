"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.database import init_db
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.scheduler.jobs import setup_scheduler, shutdown_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    setup_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title=settings.app_name,
    description="Discover business opportunities from social media and trend platforms",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting - add limiter to app state and middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


# Import and include routers
from app.api import (
    dashboard,
    opportunities,
    scrape,
    settings as settings_router,
    export,
    validation,
    validation_tools,
    auth,
    alerts,
    saved_searches,
    app_store,
    app_store_saved_searches,
)
from app.websockets import endpoints as websocket_router

auth_dependency = [Depends(verify_api_key)]

app.include_router(
    auth.router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"]
)
app.include_router(
    alerts.router,
    prefix=f"{settings.api_prefix}/alerts",
    tags=["Alerts"],
    dependencies=auth_dependency,
)
app.include_router(
    saved_searches.router,
    prefix=f"{settings.api_prefix}/saved-searches",
    tags=["Saved Searches"],
    dependencies=auth_dependency,
)
app.include_router(
    dashboard.router,
    prefix=f"{settings.api_prefix}/dashboard",
    tags=["Dashboard"],
    dependencies=auth_dependency,
)
app.include_router(
    opportunities.router,
    prefix=f"{settings.api_prefix}/opportunities",
    tags=["Opportunities"],
    dependencies=auth_dependency,
)
app.include_router(
    scrape.router,
    prefix=f"{settings.api_prefix}/scrape",
    tags=["Scraping"],
    dependencies=auth_dependency,
)
app.include_router(
    settings_router.router,
    prefix=f"{settings.api_prefix}/settings",
    tags=["Settings"],
    dependencies=auth_dependency,
)
app.include_router(
    export.router,
    prefix=f"{settings.api_prefix}/export",
    tags=["Export"],
    dependencies=auth_dependency,
)
app.include_router(
    validation.router,
    prefix=f"{settings.api_prefix}/validation",
    tags=["Validation"],
    dependencies=auth_dependency,
)
app.include_router(
    validation_tools.router,
    prefix=f"{settings.api_prefix}/validation-tools",
    tags=["Validation Tools"],
    dependencies=auth_dependency,
)
app.include_router(
    app_store.router,
    prefix=f"{settings.api_prefix}",
    tags=["App Store"],
    dependencies=auth_dependency,
)
app.include_router(
    app_store_saved_searches.router,
    prefix=f"{settings.api_prefix}",
    tags=["App Store Saved Searches"],
    dependencies=auth_dependency,
)

app.include_router(websocket_router.websocket_router)
