"""initial persistence schema

Revision ID: 20260731_0001
Revises: None
Create Date: 2026-07-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260731_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clinic_days",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("clinic_id", sa.String(length=100), nullable=False),
        sa.Column("clinic_name", sa.String(length=200), nullable=True),
        sa.Column("clinic_location", sa.String(length=300), nullable=True),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("received_rows", sa.Integer(), nullable=False),
        sa.Column("accepted_rows", sa.Integer(), nullable=False),
        sa.Column("rejected_rows", sa.Integer(), nullable=False),
        sa.Column("source_hash", sa.String(length=71), nullable=False),
        sa.Column("report_hash", sa.String(length=71), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "business_date", name="uq_clinic_day"),
    )
    op.create_index("ix_clinic_days_business_date", "clinic_days", ["business_date"])
    op.create_index("ix_clinic_days_clinic_business_date", "clinic_days", ["clinic_id", "business_date"])
    op.create_index("ix_clinic_days_clinic_id", "clinic_days", ["clinic_id"])

    op.create_table(
        "visits",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("clinic_day_id", sa.String(length=36), nullable=False),
        sa.Column("visit_id", sa.String(length=120), nullable=False),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("doctor_id", sa.String(length=120), nullable=False),
        sa.Column("payment_mode", sa.String(length=10), nullable=False),
        sa.Column("amount_paid_paise", sa.Integer(), nullable=False),
        sa.Column("discount_paise", sa.Integer(), nullable=False),
        sa.Column("is_refund", sa.Boolean(), nullable=False),
        sa.Column("gross_line_total_paise", sa.Integer(), nullable=False),
        sa.Column("billed_paise", sa.Integer(), nullable=False),
        sa.Column("outstanding_paise", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["clinic_day_id"], ["clinic_days.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_day_id", "visit_id", name="uq_visit_per_day"),
    )
    op.create_index("ix_visits_clinic_day_id", "visits", ["clinic_day_id"])
    op.create_index("ix_visits_payment_mode", "visits", ["payment_mode"])
    op.create_index("ix_visits_timestamp_utc", "visits", ["timestamp_utc"])

    op.create_table(
        "ingestion_errors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("clinic_day_id", sa.String(length=36), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.String(length=120), nullable=True),
        sa.Column("field_path", sa.String(length=300), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_row_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["clinic_day_id"], ["clinic_days.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_errors_clinic_day_id", "ingestion_errors", ["clinic_day_id"])
    op.create_index("ix_ingestion_errors_clinic_day_row", "ingestion_errors", ["clinic_day_id", "row_index"])

    op.create_table(
        "narratives",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("clinic_day_id", sa.String(length=36), nullable=False),
        sa.Column("report_hash", sa.String(length=71), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("traces_json", sa.JSON(), nullable=False),
        sa.Column("unavailable_metrics_json", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=150), nullable=True),
        sa.Column("generation_ms", sa.Integer(), nullable=True),
        sa.Column("fallback_reason_code", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["clinic_day_id"], ["clinic_days.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_day_id", name="uq_narrative_per_day"),
    )
    op.create_index("ix_narratives_clinic_day_id", "narratives", ["clinic_day_id"])

    op.create_table(
        "line_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("visit_id", sa.String(length=36), nullable=False),
        sa.Column("drug_name_source", sa.String(length=200), nullable=False),
        sa.Column("drug_name_normalized", sa.String(length=200), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("unit_price_paise", sa.Integer(), nullable=False),
        sa.Column("gross_revenue_paise", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_line_items_drug_name_normalized", "line_items", ["drug_name_normalized"])
    op.create_index("ix_line_items_visit_id", "line_items", ["visit_id"])


def downgrade() -> None:
    op.drop_index("ix_line_items_visit_id", table_name="line_items")
    op.drop_index("ix_line_items_drug_name_normalized", table_name="line_items")
    op.drop_table("line_items")

    op.drop_index("ix_narratives_clinic_day_id", table_name="narratives")
    op.drop_table("narratives")

    op.drop_index("ix_ingestion_errors_clinic_day_row", table_name="ingestion_errors")
    op.drop_index("ix_ingestion_errors_clinic_day_id", table_name="ingestion_errors")
    op.drop_table("ingestion_errors")

    op.drop_index("ix_visits_timestamp_utc", table_name="visits")
    op.drop_index("ix_visits_payment_mode", table_name="visits")
    op.drop_index("ix_visits_clinic_day_id", table_name="visits")
    op.drop_table("visits")

    op.drop_index("ix_clinic_days_clinic_id", table_name="clinic_days")
    op.drop_index("ix_clinic_days_clinic_business_date", table_name="clinic_days")
    op.drop_index("ix_clinic_days_business_date", table_name="clinic_days")
    op.drop_table("clinic_days")
