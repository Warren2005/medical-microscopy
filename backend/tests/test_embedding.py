"""
Tests for the CLIP embedding service.

Tests marked with @pytest.mark.slow require model loading (~5s).
Run with: pytest -m slow
"""

import math
import pytest

from app.services.embedding import EmbeddingService


def test_model_name_conversion():
    """ViT-B/32 is converted to ViT-B-32 for open_clip."""
    service = EmbeddingService("ViT-B/32", "cpu")
    assert service.clip_model_name == "ViT-B-32"


def test_model_name_no_slash():
    """Names without slashes pass through unchanged."""
    service = EmbeddingService("ViT-B-32", "cpu")
    assert service.clip_model_name == "ViT-B-32"


def test_health_check_before_load():
    """Health check returns False before model is loaded."""
    service = EmbeddingService("ViT-B/32", "cpu")
    assert service.health_check() is False


@pytest.mark.slow
@pytest.mark.asyncio
async def test_health_check_after_load():
    """Health check returns True after model is loaded."""
    service = EmbeddingService("ViT-B/32", "cpu")
    await service.load_model()
    assert service.health_check() is True


@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_embedding_returns_512_dim():
    """Embedding is exactly 512 dimensions."""
    service = EmbeddingService("ViT-B/32", "cpu")
    await service.load_model()

    # Create a minimal test image (red 64x64 JPEG)
    from PIL import Image
    import io
    img = Image.new("RGB", (64, 64), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    embedding = await service.get_embedding(image_bytes)
    assert len(embedding) == 512


@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_embedding_is_normalized():
    """Embedding vector has unit L2 norm."""
    service = EmbeddingService("ViT-B/32", "cpu")
    await service.load_model()

    from PIL import Image
    import io
    img = Image.new("RGB", (64, 64), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    embedding = await service.get_embedding(image_bytes)
    magnitude = math.sqrt(sum(x ** 2 for x in embedding))
    assert abs(magnitude - 1.0) < 1e-4


@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_embedding_deterministic():
    """Same image produces identical embeddings."""
    service = EmbeddingService("ViT-B/32", "cpu")
    await service.load_model()

    from PIL import Image
    import io
    img = Image.new("RGB", (64, 64), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    emb1 = await service.get_embedding(image_bytes)
    emb2 = await service.get_embedding(image_bytes)
    assert emb1 == emb2
