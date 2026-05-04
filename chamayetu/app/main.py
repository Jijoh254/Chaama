"""
ChamaYetu - Main FastAPI Application

This is the entry point for the ChamaYetu application.
Sets up FastAPI app, middleware, routers, and static files.
"""
from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import engine, Base
from app.routers import auth, dashboard, groups, contributions, payouts, notifications, mpesa_webhooks, admin_dashboard
from app.core.config import settings


# Create database tables on startup (for development)
# In production, use Alembic migrations instead
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - creates tables on startup."""
    # Startup: Create all tables if they don't exist
    # Note: In production, use `alembic upgrade head` instead
    if settings.APP_ENV == "development":
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created (development mode)")
    
    yield
    
    # Shutdown: cleanup if needed
    print("👋 Application shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Digital Chama (ROSCA) platform for families and groups in Kenya",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - allow requests from same origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
# Normalize path to handle relative paths correctly
static_path = os.path.normpath(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "app": settings.APP_NAME}


# Root redirect to dashboard
@app.get("/")
async def root():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard")


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(contributions.router, prefix="/contributions", tags=["Contributions"])
app.include_router(payouts.router, prefix="/payouts", tags=["Payouts"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(mpesa_webhooks.router, prefix="/mpesa", tags=["M-Pesa Webhooks"])
app.include_router(admin_dashboard.router, prefix="/admin", tags=["Admin Dashboard"])

# API routes (must be included after main routers to avoid conflicts)
# Note: The /api/notifications/* endpoints are defined in notifications.py with full paths


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions gracefully."""
    # Log the error (in production, use proper logging)
    print(f"❌ Unhandled exception: {exc}")
    
    # For API routes, return JSON
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
    
    # For web pages, re-raise or show error page
    raise exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.APP_ENV == "development" else False
    )
