"""
Similarity search endpoint.

POST /api/v1/search/similar
Accepts an image file, generates CLIP embedding on-the-fly,
searches Qdrant for top-N similar vectors, fetches metadata
from PostgreSQL, and returns results with presigned URLs.
"""

import time
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, Query, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select

from app.core.errors import ValidationError
from app.models.feedback import Feedback
from app.models.image import Image
from app.schemas.search import SearchResponse, SearchResult
from app.schemas.image import ImageResponse
from app.services.database import db_service
from app.services.embedding import embedding_service
from app.services.qdrant import qdrant_service
from app.services.storage import storage_service
from app.services.search_helpers import build_qdrant_filter

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/tiff"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/similar", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_similar(
    request: Request,
    file: UploadFile = File(...),
    limit: int = Query(default=30, ge=1, le=100),
    diagnosis: Optional[str] = Query(default=None),
    tissue_type: Optional[str] = Query(default=None),
    benign_malignant: Optional[str] = Query(default=None),
):
    """Accept an image and return the top-N most visually similar images."""
    total_start = time.time()

    # Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            "Unsupported file type. Use JPEG, PNG, or TIFF.",
            details={"content_type": file.content_type},
        )

    # Read and validate size
    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise ValidationError(
            f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB.",
            details={"size_bytes": len(image_bytes)},
        )

    # Generate embedding
    embed_start = time.time()
    embedding = await embedding_service.get_embedding(image_bytes)
    embed_time = (time.time() - embed_start) * 1000

    # Build filter and search Qdrant
    query_filter = build_qdrant_filter(diagnosis, tissue_type, benign_malignant)
    search_start = time.time()
    qdrant_results = await qdrant_service.search(
        vector=embedding, limit=limit, query_filter=query_filter
    )
    search_time = (time.time() - search_start) * 1000

    # Fetch metadata from PostgreSQL and feedback scores
    if qdrant_results:
        image_ids = [UUID(str(point.id)) for point in qdrant_results]
        async with db_service.get_session() as session:
            stmt = select(Image).where(Image.id.in_(image_ids))
            result = await session.execute(stmt)
            images_by_id = {img.id: img for img in result.scalars().all()}

            # Fetch net feedback votes per result image
            fb_stmt = (
                select(
                    Feedback.result_image_id,
                    func.sum(Feedback.vote).label("net_vote"),
                )
                .where(Feedback.result_image_id.in_(image_ids))
                .group_by(Feedback.result_image_id)
            )
            fb_result = await session.execute(fb_stmt)
            feedback_scores = {row.result_image_id: row.net_vote for row in fb_result}
    else:
        images_by_id = {}
        feedback_scores = {}

    # Build response with presigned URLs and feedback-adjusted scores
    FEEDBACK_WEIGHT = 0.02
    results = []
    for point in qdrant_results:
        image = images_by_id.get(UUID(str(point.id)))
        if image:
            net_vote = feedback_scores.get(image.id, 0)
            adjusted_score = point.score + (net_vote * FEEDBACK_WEIGHT)
            adjusted_score = max(0.0, min(1.0, adjusted_score))
            results.append(
                SearchResult(
                    image=ImageResponse.model_validate(image),
                    similarity_score=round(adjusted_score, 6),
                    image_url=f"/api/v1/images/{image.id}/file",
                )
            )

    # Re-sort by adjusted score
    results.sort(key=lambda r: r.similarity_score, reverse=True)

    total_time = (time.time() - total_start) * 1000
    return SearchResponse(
        query_processing_time_ms=round(embed_time, 1),
        search_time_ms=round(search_time, 1),
        total_time_ms=round(total_time, 1),
        results=results,
        result_count=len(results),
    )
