"""Create images table.

Revision ID: 001
Revises:
Create Date: 2026-02-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "images",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("dataset_source", sa.String(50), nullable=True),
        sa.Column("image_path", sa.String(500), nullable=False),
        sa.Column("diagnosis", sa.String(100), nullable=True),
        sa.Column("tissue_type", sa.String(50), nullable=True),
        sa.Column("benign_malignant", sa.String(20), nullable=True),
        sa.Column("age", sa.Integer, nullable=True),
        sa.Column("sex", sa.String(10), nullable=True),
        sa.Column(
            "created_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime, server_default=sa.text("NOW()"), nullable=False
        ),
    )
    op.create_index("idx_diagnosis", "images", ["diagnosis"])
    op.create_index("idx_tissue_type", "images", ["tissue_type"])


def downgrade() -> None:
    op.drop_index("idx_tissue_type", table_name="images")
    op.drop_index("idx_diagnosis", table_name="images")
    op.drop_table("images")
