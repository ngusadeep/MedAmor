"""Audit report model: structured output from audit engine."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditStatus:
    """Audit result status."""

    NO_FINDINGS = "NO_FINDINGS"
    FINDING_PRESENT = "FINDING_PRESENT"


class AuditReport(Base):
    """Stored audit report linked to a job."""

    __tablename__ = "audit_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # NO_FINDINGS | FINDING_PRESENT
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    corrective_actions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    next_audit_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    job: Mapped["Job"] = relationship("Job", back_populates="audit_report")
