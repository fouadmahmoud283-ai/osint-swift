"""FastAPI application for SWIFT API Gateway."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import ingestion_router

app = FastAPI(
    title="SWIFT API Gateway",
    description="API Gateway for SWIFT Intelligence Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ingestion_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "swift-api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SWIFT API Gateway",
        "docs": "/docs",
        "health": "/health",
        "dashboard": "/dashboard"
    }


@app.get("/dashboard")
@app.get("/dashboard/")
async def dashboard():
    """Dashboard UI for API testing and visualization."""
    return FileResponse(STATIC_DIR / "dashboard.html")
