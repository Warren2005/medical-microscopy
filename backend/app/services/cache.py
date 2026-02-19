"""Redis caching service for embedding vectors."""

import hashlib
import json
from typing import Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging_config import logger


class CacheService:
    def __init__(self, redis_url: str, ttl_hours: int = 24):
        self._redis_url = redis_url
        self._ttl_seconds = ttl_hours * 3600
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        self._client = redis.from_url(self._redis_url, decode_responses=True)
        await self._client.ping()
        logger.info("Connected to Redis", extra={"url": self._redis_url})

    async def disconnect(self):
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Redis")

    async def health_check(self) -> bool:
        if not self._client:
            return False
        await self._client.ping()
        return True

    @staticmethod
    def hash_image(image_bytes: bytes) -> str:
        return hashlib.sha256(image_bytes).hexdigest()

    async def get_embedding(self, image_hash: str) -> Optional[list[float]]:
        if not self._client:
            return None
        data = await self._client.get(f"emb:{image_hash}")
        if data:
            return json.loads(data)
        return None

    async def set_embedding(self, image_hash: str, embedding: list[float]):
        if not self._client:
            return
        await self._client.setex(
            f"emb:{image_hash}",
            self._ttl_seconds,
            json.dumps(embedding),
        )


cache_service = CacheService(
    redis_url=settings.redis_url,
    ttl_hours=settings.cache_ttl_hours,
)
