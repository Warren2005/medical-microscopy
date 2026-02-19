"""
Batch search endpoint.

POST /api/v1/search/batch — Accept a zip file of images, process in parallel.
GET /api/v1/jobs/{job_id} — Poll job status and retrieve results.
"""

import asyncio
import io
import json
import time
import uuid
import zipfile
from typing import Optional

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from uuid import UUID

from app.core.errors import ValidationError
from app.core.logging_config import logger
from app.models.image import Image
from app.schemas.image import ImageResponse
from app.services.database import db_service
from app.services.embedding import embedding_service
from app.services.qdrant import qdrant_service
from app.services.storage import storage_service
from app.services.search_helpers import build_qdrant_filter

router = APIRouter()

# In-memory job store (for production, use Redis or a database)
_jobs: dict[str, dict] = {}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
MAX_BATCH_SIZE = 200 * 1024 * 1024  # 200MB for zip


class BatchJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class BatchJobStatus(BaseModel):
    job_id: str
    status: str  # "processing" | "completed" | "failed"
    total_images: int
    processed_images: int
    results: Optional[list] = None
    error: Optional[str] = None
    elapsed_ms: Optional[float] = None


@router.post("/batch", response_model=BatchJobResponse)
async def batch_search(
    file: UploadFile = File(...),
    limit: int = Query(default=5, ge=1, le=20),
    diagnosis: Optional[str] = Query(default=None),
    tissue_type: Optional[str] = Query(default=None),
    benign_malignant: Optional[str] = Query(default=None),
):
    """Accept a zip file of images and process in background."""
    # Read zip file
    zip_bytes = await file.read()
    if len(zip_bytes) > MAX_BATCH_SIZE:
        raise ValidationError(
            f"Zip file too large. Maximum size is {MAX_BATCH_SIZE // (1024 * 1024)}MB.",
            details={"size_bytes": len(zip_bytes)},
        )

    # Validate it's a zip file
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise ValidationError("File must be a valid ZIP archive.")

    # Extract image files
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    image_entries = [
        name for name in zf.namelist()
        if any(name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)
        and not name.startswith("__MACOSX")
    ]

    if not image_entries:
        raise ValidationError("No valid image files found in ZIP archive.")

    # Create job
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "processing",
        "total_images": len(image_entries),
        "processed_images": 0,
        "results": [],
        "error": None,
        "start_time": time.time(),
    }

    # Process in background
    asyncio.create_task(
        _process_batch(job_id, zf, image_entries, limit, diagnosis, tissue_type, benign_malignant)
    )

    return BatchJobResponse(
        job_id=job_id,
        status="processing",
        message=f"Processing {len(image_entries)} images. Poll GET /api/v1/search/jobs/{job_id} for status.",
    )


async def _process_batch(
    job_id: str,
    zf: zipfile.ZipFile,
    image_entries: list[str],
    limit: int,
    diagnosis: Optional[str],
    tissue_type: Optional[str],
    benign_malignant: Optional[str],
):
    """Process a batch of images in parallel."""
    job = _jobs[job_id]
    query_filter = build_qdrant_filter(diagnosis, tissue_type, benign_malignant)

    async def process_single(filename: str) -> dict:
        image_bytes = zf.read(filename)
        embedding = await embedding_service.get_embedding(image_bytes)
        qdrant_results = await qdrant_service.search(
            vector=embedding, limit=limit, query_filter=query_filter
        )

        results = []
        if qdrant_results:
            image_ids = [UUID(str(point.id)) for point in qdrant_results]
            async with db_service.get_session() as session:
                stmt = select(Image).where(Image.id.in_(image_ids))
                result = await session.execute(stmt)
                images_by_id = {img.id: img for img in result.scalars().all()}

            for point in qdrant_results:
                image = images_by_id.get(UUID(str(point.id)))
                if image:
                    results.append({
                        "image_id": str(image.id),
                        "diagnosis": image.diagnosis,
                        "similarity_score": point.score,
                    })

        return {
            "query_filename": filename,
            "results": results,
        }

    try:
        # Process images with controlled concurrency (4 at a time)
        semaphore = asyncio.Semaphore(4)

        async def process_with_semaphore(filename: str) -> dict:
            async with semaphore:
                result = await process_single(filename)
                job["processed_images"] += 1
                return result

        tasks = [process_with_semaphore(f) for f in image_entries]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        job["results"] = [
            r for r in batch_results if isinstance(r, dict)
        ]
        job["status"] = "completed"
        job["elapsed_ms"] = round((time.time() - job["start_time"]) * 1000, 1)

    except Exception as e:
        logger.error(f"Batch job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)


@router.get("/jobs/{job_id}", response_model=BatchJobStatus)
async def get_job_status(job_id: str):
    """Check the status of a batch search job."""
    job = _jobs.get(job_id)
    if not job:
        raise ValidationError(
            "Job not found.",
            details={"job_id": job_id},
        )

    return BatchJobStatus(
        job_id=job_id,
        status=job["status"],
        total_images=job["total_images"],
        processed_images=job["processed_images"],
        results=job["results"] if job["status"] == "completed" else None,
        error=job.get("error"),
        elapsed_ms=job.get("elapsed_ms"),
    )
