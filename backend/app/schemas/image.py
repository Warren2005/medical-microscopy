"""Pydantic models for image metadata."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImageBase(BaseModel):
    dataset_source: Optional[str] = None
    image_path: str
    diagnosis: Optional[str] = None
    tissue_type: Optional[str] = None
    benign_malignant: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None


class ImageCreate(ImageBase):
    pass


class ImageResponse(ImageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
