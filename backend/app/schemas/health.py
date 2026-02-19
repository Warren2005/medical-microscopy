"""Pydantic models for health check responses."""

from pydantic import BaseModel


class ServiceStatus(BaseModel):
    api: str
    postgres: str
    qdrant: str
    minio: str
    clip: str
    redis: str


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    services: ServiceStatus
    version: str
    environment: str
    timestamp: str
