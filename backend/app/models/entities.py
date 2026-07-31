from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClinicDay(Base):
    __tablename__ = "clinic_days"
    __table_args__ = (
        UniqueConstraint("clinic_id", "business_date", name="uq_clinic_day"),
        Index("ix_clinic_days_clinic_business_date", "clinic_id", "business_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    clinic_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    clinic_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    clinic_location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    business_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    received_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    total_issue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    returned_issue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issues_truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    report_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    report_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    visits: Mapped[list[Visit]] = relationship(back_populates="clinic_day", cascade="all, delete-orphan")
    ingestion_errors: Mapped[list[IngestionError]] = relationship(back_populates="clinic_day", cascade="all, delete-orphan")
    narrative: Mapped[Narrative | None] = relationship(back_populates="clinic_day", cascade="all, delete-orphan", uselist=False)


class Visit(Base):
    __tablename__ = "visits"
    __table_args__ = (
        UniqueConstraint("clinic_day_id", "visit_id", name="uq_visit_per_day"),
        Index("ix_visits_timestamp_utc", "timestamp_utc"),
        Index("ix_visits_payment_mode", "payment_mode"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    clinic_day_id: Mapped[str] = mapped_column(ForeignKey("clinic_days.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_id: Mapped[str] = mapped_column(String(120), nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(120), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(10), nullable=False)
    amount_paid_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    is_refund: Mapped[bool] = mapped_column(Boolean, nullable=False)
    gross_line_total_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    billed_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    outstanding_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    clinic_day: Mapped[ClinicDay] = relationship(back_populates="visits")
    line_items: Mapped[list[LineItem]] = relationship(back_populates="visit", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    visit_id: Mapped[str] = mapped_column(ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_name_source: Mapped[str] = mapped_column(String(200), nullable=False)
    drug_name_normalized: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    gross_revenue_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    visit: Mapped[Visit] = relationship(back_populates="line_items")


class IngestionError(Base):
    __tablename__ = "ingestion_errors"
    __table_args__ = (Index("ix_ingestion_errors_clinic_day_row", "clinic_day_id", "row_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    clinic_day_id: Mapped[str] = mapped_column(ForeignKey("clinic_days.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    visit_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    field_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    error_code: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_row_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    clinic_day: Mapped[ClinicDay] = relationship(back_populates="ingestion_errors")


class Narrative(Base):
    __tablename__ = "narratives"
    __table_args__ = (UniqueConstraint("clinic_day_id", name="uq_narrative_per_day"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    clinic_day_id: Mapped[str] = mapped_column(ForeignKey("clinic_days.id", ondelete="CASCADE"), nullable=False, index=True)
    report_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    traces_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    unavailable_metrics_json: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(150), nullable=True)
    generation_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fallback_reason_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    clinic_day: Mapped[ClinicDay] = relationship(back_populates="narrative")
