"""
Text-based similarity search endpoint.

POST /api/v1/search/text
Accepts a text query, generates CLIP text embedding,
searches Qdrant for top-N similar vectors, fetches metadata
from PostgreSQL, and returns results with presigned URLs.
"""

import time
from typing import Optional
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.models.image import Image
from app.schemas.search import SearchResponse, SearchResult
from app.schemas.image import ImageResponse
from app.services.database import db_service
from app.services.embedding import embedding_service
from app.services.qdrant import qdrant_service
from app.services.storage import storage_service
from app.services.search_helpers import build_qdrant_filter

router = APIRouter()


class TextSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)
    diagnosis: Optional[str] = None
    tissue_type: Optional[str] = None
    benign_malignant: Optional[str] = None


@router.post("/text", response_model=SearchResponse)
async def search_by_text(body: TextSearchRequest):
    """Accept a text query and return the top-N most visually similar images."""
    total_start = time.time()

    # Generate text embedding
    embed_start = time.time()
    embedding = await embedding_service.get_text_embedding(body.query)
    embed_time = (time.time() - embed_start) * 1000

    # Build filter and search Qdrant
    query_filter = build_qdrant_filter(
        body.diagnosis, body.tissue_type, body.benign_malignant
    )
    search_start = time.time()
    qdrant_results = await qdrant_service.search(
        vector=embedding, limit=body.top_k, query_filter=query_filter
    )
    search_time = (time.time() - search_start) * 1000

    # Fetch metadata from PostgreSQL
    if qdrant_results:
        image_ids = [UUID(str(point.id)) for point in qdrant_results]
        async with db_service.get_session() as session:
            stmt = select(Image).where(Image.id.in_(image_ids))
            result = await session.execute(stmt)
            images_by_id = {img.id: img for img in result.scalars().all()}
    else:
        images_by_id = {}

    # Build response with presigned URLs
    results = []
    for point in qdrant_results:
        image = images_by_id.get(UUID(str(point.id)))
        if image:
            url = storage_service.get_presigned_url(image.image_path)
            results.append(
                SearchResult(
                    image=ImageResponse.model_validate(image),
                    similarity_score=point.score,
                    image_url=url,
                )
            )

    total_time = (time.time() - total_start) * 1000
    return SearchResponse(
        query_processing_time_ms=round(embed_time, 1),
        search_time_ms=round(search_time, 1),
        total_time_ms=round(total_time, 1),
        results=results,
        result_count=len(results),
    )
