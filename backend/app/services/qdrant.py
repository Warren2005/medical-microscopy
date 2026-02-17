"""
Qdrant vector database client wrapper.

Provides:
- Collection management (create if not exists)
- Vector search with optional metadata filters
- Upsert for adding/updating vectors
- Health check
"""

from typing import Optional
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    Filter,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from app.core.config import settings
from app.core.logging_config import logger


class QdrantService:
    def __init__(self, host: str, port: int, collection_name: str):
        self._host = host
        self._port = port
        self._collection_name = collection_name
        self._client: Optional[AsyncQdrantClient] = None

    async def connect(self):
        self._client = AsyncQdrantClient(host=self._host, port=self._port)
        logger.info(
            "Connected to Qdrant",
            extra={"host": self._host, "port": self._port},
        )

    async def disconnect(self):
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Qdrant")

    async def health_check(self) -> bool:
        await self._client.get_collections()
        return True

    async def ensure_collection(self, vector_size: int = 512):
        collections = await self._client.get_collections()
        existing = [c.name for c in collections.collections]
        if self._collection_name not in existing:
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=vector_size, distance=Distance.COSINE
                ),
            )
            # Create payload indexes for filtered search
            for field in ["diagnosis", "tissue_type", "benign_malignant", "dataset"]:
                await self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name=field,
                    field_schema="keyword",
                )
            logger.info(
                "Created Qdrant collection",
                extra={"collection": self._collection_name, "vector_size": vector_size},
            )
        else:
            logger.info(
                "Qdrant collection already exists",
                extra={"collection": self._collection_name},
            )

    async def search(
        self,
        vector: list[float],
        limit: int = 10,
        query_filter: Optional[Filter] = None,
    ) -> list[ScoredPoint]:
        return await self._client.search(
            collection_name=self._collection_name,
            query_vector=vector,
            query_filter=query_filter,
            limit=limit,
        )

    async def upsert(self, id: str, vector: list[float], payload: dict):
        await self._client.upsert(
            collection_name=self._collection_name,
            points=[PointStruct(id=id, vector=vector, payload=payload)],
        )


qdrant_service = QdrantService(
    host=settings.qdrant_host,
    port=settings.qdrant_port,
    collection_name=settings.qdrant_collection_name,
)
