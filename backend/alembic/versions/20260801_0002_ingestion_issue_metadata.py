"""add ingestion issue metadata

Revision ID: 20260801_0002
Revises: 20260731_0001
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_0002"
down_revision: Union[str, None] = "20260731_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clinic_days", sa.Column("total_issue_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("clinic_days", sa.Column("returned_issue_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("clinic_days", sa.Column("issues_truncated", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("clinic_days", "issues_truncated")
    op.drop_column("clinic_days", "returned_issue_count")
    op.drop_column("clinic_days", "total_issue_count")
