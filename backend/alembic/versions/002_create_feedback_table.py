"""Create feedback table.

Revision ID: 002
Revises: 001
Create Date: 2026-02-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("query_image_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result_image_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vote", sa.Integer, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False
        ),
    )
    op.create_index("idx_feedback_query_image", "feedback", ["query_image_id"])
    op.create_index("idx_feedback_result_image", "feedback", ["result_image_id"])


def downgrade() -> None:
    op.drop_index("idx_feedback_result_image", table_name="feedback")
    op.drop_index("idx_feedback_query_image", table_name="feedback")
    op.drop_table("feedback")
