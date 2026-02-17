"""
SQLAlchemy ORM model for the images table.

Maps to the PostgreSQL schema:
- UUID primary key (generated server-side)
- Metadata fields for diagnosis, tissue type, etc.
- Indexes on frequently filtered columns
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Image(Base):
    __tablename__ = "images"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    dataset_source: Mapped[Optional[str]] = mapped_column(String(50))
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    diagnosis: Mapped[Optional[str]] = mapped_column(String(100))
    tissue_type: Mapped[Optional[str]] = mapped_column(String(50))
    benign_malignant: Mapped[Optional[str]] = mapped_column(String(20))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    sex: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("NOW()")
    )

    __table_args__ = (
        Index("idx_diagnosis", "diagnosis"),
        Index("idx_tissue_type", "tissue_type"),
    )
