"""
DICOM search endpoint.

POST /api/v1/search/dicom
Accepts a DICOM file, extracts pixel data and metadata,
generates CLIP embedding, and searches for similar images.
"""

import time
from typing import Optional

from fastapi import APIRouter, File, Query, UploadFile
from sqlalchemy import select
from uuid import UUID

from app.core.errors import ValidationError
from app.models.image import Image
from app.schemas.search import SearchResponse, SearchResult
from app.schemas.image import ImageResponse
from app.services.database import db_service
from app.services.embedding import embedding_service
from app.services.qdrant import qdrant_service
from app.services.storage import storage_service
from app.services.search_helpers import build_qdrant_filter
from app.services.dicom import dicom_service

router = APIRouter()

ALLOWED_DICOM_TYPES = {"application/dicom", "application/octet-stream"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB for DICOM


@router.post("/dicom", response_model=SearchResponse)
async def search_dicom(
    file: UploadFile = File(...),
    limit: int = Query(default=10, ge=1, le=50),
    diagnosis: Optional[str] = Query(default=None),
    tissue_type: Optional[str] = Query(default=None),
    benign_malignant: Optional[str] = Query(default=None),
):
    """Accept a DICOM file and return the top-N most visually similar images."""
    total_start = time.time()

    # Read file
    dicom_bytes = await file.read()
    if len(dicom_bytes) > MAX_FILE_SIZE:
        raise ValidationError(
            f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB.",
            details={"size_bytes": len(dicom_bytes)},
        )

    # Extract image from DICOM
    try:
        image_bytes = dicom_service.extract_image(dicom_bytes)
        metadata = dicom_service.extract_metadata(dicom_bytes)
    except Exception as e:
        raise ValidationError(
            "Failed to parse DICOM file. Ensure it is a valid DICOM image.",
            details={"error": str(e)},
        )

    # Generate embedding
    embed_start = time.time()
    embedding = await embedding_service.get_embedding(image_bytes)
    embed_time = (time.time() - embed_start) * 1000

    # Search Qdrant
    query_filter = build_qdrant_filter(diagnosis, tissue_type, benign_malignant)
    search_start = time.time()
    qdrant_results = await qdrant_service.search(
        vector=embedding, limit=limit, query_filter=query_filter
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

    # Build response
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
