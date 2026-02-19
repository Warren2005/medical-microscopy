"""
Health check endpoint.

Checks connectivity to all backend services:
- PostgreSQL
- Qdrant
- MinIO
"""

from fastapi import APIRouter
from datetime import datetime

from app.core.config import settings
from app.core.logging_config import logger
from app.schemas.health import HealthResponse, ServiceStatus
from app.services.database import db_service
from app.services.qdrant import qdrant_service
from app.services.storage import storage_service
from app.services.embedding import embedding_service
from app.services.cache import cache_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check — returns status of all backend services.

    Overall status:
    - "healthy" if all services are up
    - "degraded" if some services are down
    - "unhealthy" if all external services are down
    """
    service_checks = {"api": "up"}

    # Check PostgreSQL
    try:
        await db_service.health_check()
        service_checks["postgres"] = "up"
    except Exception:
        service_checks["postgres"] = "down"

    # Check Qdrant
    try:
        await qdrant_service.health_check()
        service_checks["qdrant"] = "up"
    except Exception:
        service_checks["qdrant"] = "down"

    # Check MinIO
    try:
        service_checks["minio"] = "up" if storage_service.health_check() else "down"
    except Exception:
        service_checks["minio"] = "down"

    # Check CLIP model
    try:
        service_checks["clip"] = "up" if embedding_service.health_check() else "down"
    except Exception:
        service_checks["clip"] = "down"

    # Check Redis
    try:
        service_checks["redis"] = "up" if await cache_service.health_check() else "down"
    except Exception:
        service_checks["redis"] = "down"

    # Determine overall status
    external_services = ["postgres", "qdrant", "minio"]
    up_count = sum(1 for s in external_services if service_checks[s] == "up")

    if up_count == len(external_services):
        overall = "healthy"
    elif up_count == 0:
        overall = "unhealthy"
    else:
        overall = "degraded"

    return HealthResponse(
        status=overall,
        services=ServiceStatus(**service_checks),
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )
