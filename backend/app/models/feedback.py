"""SQLAlchemy ORM model for the feedback table."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    query_image_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    result_image_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    vote: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("NOW()")
    )

    __table_args__ = (
        Index("idx_feedback_query_image", "query_image_id"),
        Index("idx_feedback_result_image", "result_image_id"),
    )
