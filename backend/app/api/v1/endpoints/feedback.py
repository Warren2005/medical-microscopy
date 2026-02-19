"""
Pathologist feedback endpoints.

POST /api/v1/feedback — submit a vote on a search result
GET  /api/v1/feedback/stats — aggregate feedback statistics
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.models.feedback import Feedback
from app.services.database import db_service

router = APIRouter()


class FeedbackRequest(BaseModel):
    query_image_id: Optional[UUID] = None
    result_image_id: UUID
    vote: int = Field(..., ge=-1, le=1)


class FeedbackResponse(BaseModel):
    id: UUID
    query_image_id: Optional[UUID]
    result_image_id: UUID
    vote: int


class FeedbackStats(BaseModel):
    total: int
    upvotes: int
    downvotes: int


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest):
    """Record a pathologist's vote on a search result."""
    async with db_service.get_session() as session:
        fb = Feedback(
            query_image_id=body.query_image_id,
            result_image_id=body.result_image_id,
            vote=body.vote,
        )
        session.add(fb)
        await session.commit()
        await session.refresh(fb)
        return FeedbackResponse(
            id=fb.id,
            query_image_id=fb.query_image_id,
            result_image_id=fb.result_image_id,
            vote=fb.vote,
        )


@router.get("/stats", response_model=FeedbackStats)
async def feedback_stats():
    """Return aggregate feedback statistics."""
    async with db_service.get_session() as session:
        total_q = await session.execute(select(func.count(Feedback.id)))
        total = total_q.scalar_one()

        up_q = await session.execute(
            select(func.count(Feedback.id)).where(Feedback.vote == 1)
        )
        upvotes = up_q.scalar_one()

        down_q = await session.execute(
            select(func.count(Feedback.id)).where(Feedback.vote == -1)
        )
        downvotes = down_q.scalar_one()

        return FeedbackStats(total=total, upvotes=upvotes, downvotes=downvotes)
