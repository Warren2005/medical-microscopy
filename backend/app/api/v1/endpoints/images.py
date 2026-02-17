"""
Image detail and filter endpoints.

GET /api/v1/images/filters — distinct filter values for UI dropdowns
GET /api/v1/images/{image_id} — single image metadata + presigned URL
"""

from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.errors import NotFoundError
from app.models.image import Image
from app.schemas.image import ImageResponse
from app.schemas.search import FiltersResponse, ImageDetailResponse
from app.services.database import db_service
from app.services.storage import storage_service

router = APIRouter()


@router.get("/filters", response_model=FiltersResponse)
async def get_filters():
    """Return distinct values for diagnosis, tissue_type, benign_malignant."""
    async with db_service.get_session() as session:
        diagnoses = (
            await session.execute(select(Image.diagnosis).distinct())
        ).scalars().all()
        tissue_types = (
            await session.execute(select(Image.tissue_type).distinct())
        ).scalars().all()
        classifications = (
            await session.execute(select(Image.benign_malignant).distinct())
        ).scalars().all()

    return FiltersResponse(
        diagnoses=[d for d in diagnoses if d],
        tissue_types=[t for t in tissue_types if t],
        benign_malignant=[c for c in classifications if c],
    )


@router.get("/{image_id}", response_model=ImageDetailResponse)
async def get_image(image_id: UUID):
    """Fetch a single image's metadata and presigned URL."""
    async with db_service.get_session() as session:
        image = await session.get(Image, image_id)
        if not image:
            raise NotFoundError(
                f"Image {image_id} not found",
                details={"image_id": str(image_id)},
            )
        url = storage_service.get_presigned_url(image.image_path)
        return ImageDetailResponse(
            image=ImageResponse.model_validate(image),
            image_url=url,
        )
