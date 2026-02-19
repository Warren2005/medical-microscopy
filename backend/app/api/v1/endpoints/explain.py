"""
Explainability endpoint.

POST /api/v1/explain?image_id=<uuid>
Fetches the image from MinIO, generates a GradCAM-style saliency heatmap,
and returns the overlay as a PNG.
"""

from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import Response
from sqlalchemy import select

from app.core.errors import NotFoundError
from app.models.image import Image
from app.services.database import db_service
from app.services.explainability import gradcam_service
from app.services.storage import storage_service

router = APIRouter()


@router.post("")
async def explain_image(image_id: UUID = Query(...)):
    """Generate an attention heatmap for the given image."""

    # Look up image path in database
    async with db_service.get_session() as session:
        image = await session.get(Image, image_id)
        if not image:
            raise NotFoundError(
                f"Image {image_id} not found",
                details={"image_id": str(image_id)},
            )

    # Fetch raw bytes from MinIO
    image_bytes = storage_service.get_image(image.image_path)

    # Generate heatmap
    heatmap_bytes = await gradcam_service.generate_heatmap(image_bytes)

    return Response(content=heatmap_bytes, media_type="image/png")
