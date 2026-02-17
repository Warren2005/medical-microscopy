"""
Tests for service wrappers and health endpoint integration.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.services.database import DatabaseService


def test_database_service_url_conversion():
    """Verify postgresql:// is converted to postgresql+asyncpg://."""
    service = DatabaseService("postgresql://localhost:5432/testdb")
    assert service._url == "postgresql+asyncpg://localhost:5432/testdb"


def test_database_service_url_already_async():
    """Verify postgresql+asyncpg:// is not double-converted."""
    service = DatabaseService("postgresql+asyncpg://localhost:5432/testdb")
    assert service._url == "postgresql+asyncpg://localhost:5432/testdb"


def test_health_endpoint_reports_all_services():
    """Health endpoint should report status for all services."""
    # Import app after conftest mocks are in place
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert "services" in data
    services = data["services"]
    assert "api" in services
    assert "postgres" in services
    assert "qdrant" in services
    assert "minio" in services


def test_health_healthy_when_all_up():
    """Status should be 'healthy' when all services are up."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health")
    data = response.json()

    # With default mocks, all services return healthy
    assert data["services"]["api"] == "up"
    assert "timestamp" in data
    assert "version" in data


def test_health_degraded_when_service_down():
    """Status should be 'degraded' when one service is down."""
    from app.main import app

    # Make qdrant health check fail
    with patch(
        "app.api.v1.endpoints.health.qdrant_service"
    ) as mock_qdrant:
        mock_qdrant.health_check = AsyncMock(side_effect=ConnectionError("down"))

        client = TestClient(app)
        response = client.get("/api/v1/health")
        data = response.json()

        assert data["status"] == "degraded"
        assert data["services"]["qdrant"] == "down"
