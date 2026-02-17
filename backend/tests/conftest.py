"""
Shared test fixtures and mocks.

Mocks external services so tests run without PostgreSQL, Qdrant, MinIO, or CLIP model.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def mock_services():
    """Mock all external service singletons for every test.

    Patches at all import locations so the mocks are seen
    by both main.py (lifespan) and health.py (health checks).
    """
    with (
        patch("app.main.db_service") as mock_db_main,
        patch("app.main.qdrant_service") as mock_qdrant_main,
        patch("app.main.storage_service") as mock_storage_main,
        patch("app.main.embedding_service") as mock_embed_main,
        patch("app.api.v1.endpoints.health.db_service") as mock_db_health,
        patch("app.api.v1.endpoints.health.qdrant_service") as mock_qdrant_health,
        patch("app.api.v1.endpoints.health.storage_service") as mock_storage_health,
        patch("app.api.v1.endpoints.health.embedding_service") as mock_embed_health,
    ):
        # Main lifespan mocks
        mock_db_main.connect = AsyncMock()
        mock_db_main.disconnect = AsyncMock()
        mock_qdrant_main.connect = AsyncMock()
        mock_qdrant_main.disconnect = AsyncMock()
        mock_qdrant_main.ensure_collection = AsyncMock()
        mock_storage_main.connect = MagicMock()
        mock_storage_main.disconnect = MagicMock()
        mock_embed_main.load_model = AsyncMock()

        # Health check mocks
        mock_db_health.health_check = AsyncMock(return_value=True)
        mock_qdrant_health.health_check = AsyncMock(return_value=True)
        mock_storage_health.health_check = MagicMock(return_value=True)
        mock_embed_health.health_check = MagicMock(return_value=True)

        yield {
            "db_main": mock_db_main,
            "qdrant_main": mock_qdrant_main,
            "storage_main": mock_storage_main,
            "embed_main": mock_embed_main,
            "db_health": mock_db_health,
            "qdrant_health": mock_qdrant_health,
            "storage_health": mock_storage_health,
            "embed_health": mock_embed_health,
        }
