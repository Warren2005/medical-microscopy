"""Add inspection metadata columns to images table.

Revision ID: 003
Revises: 002
Create Date: 2026-04-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("images", sa.Column("anomaly_description", sa.String(500), nullable=True))
    op.add_column("images", sa.Column("anomaly_status",      sa.String(100), nullable=True))
    op.add_column("images", sa.Column("anomaly_type",        sa.String(50),  nullable=True))
    op.add_column("images", sa.Column("identification",      sa.String(100), nullable=True))
    op.add_column("images", sa.Column("wall_location",       sa.String(50),  nullable=True))
    op.add_column("images", sa.Column("run_number",          sa.String(100), nullable=True))
    op.add_column("images", sa.Column("analysis_comment",    sa.Text,        nullable=True))
    op.add_column("images", sa.Column("analyst",             sa.String(200), nullable=True))


def downgrade() -> None:
    for col in [
        "analyst", "analysis_comment", "run_number", "wall_location",
        "identification", "anomaly_type", "anomaly_status", "anomaly_description",
    ]:
        op.drop_column("images", col)
