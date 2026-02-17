"""
FastAPI application entry point.

This file:
- Creates the FastAPI app with lifespan manager
- Configures middleware (CORS, error handling)
- Includes API routes
- Connects/disconnects services on startup/shutdown
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging_config import logger
from app.core.errors import AppException
from app.middleware.error_handler import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from app.api.v1.endpoints.router import api_router
from app.services.database import db_service
from app.services.qdrant import qdrant_service
from app.services.storage import storage_service
from app.services.embedding import embedding_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service connections on startup and shutdown."""
    # Startup
    logger.info(
        "Application starting",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
    )

    # Connect services (failures are logged but don't prevent startup)
    try:
        await db_service.connect()
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")

    try:
        await qdrant_service.connect()
        await qdrant_service.ensure_collection(vector_size=512)
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")

    try:
        storage_service.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MinIO: {e}")

    try:
        await embedding_service.load_model()
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")

    yield

    # Shutdown
    logger.info("Application shutting down")
    await db_service.disconnect()
    await qdrant_service.disconnect()
    storage_service.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for medical microscopy image similarity search",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# CORS middleware - allows frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
    }
