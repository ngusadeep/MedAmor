"""Audit job model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.audit_report import AuditReport


class JobStatus:
    """Job status constants (align with workflow: IN_PROGRESS for audit in progress)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Default audit type: project focus is breast cancer screening
AUDIT_TYPE_DEFAULT = "breast_cancer_screening"


class Job(Base):
    """Audit job: one per manual or scheduled trigger (Breast Cancer Screening focus)."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    audit_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default=AUDIT_TYPE_DEFAULT, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=JobStatus.PENDING, index=True
    )
    triggered_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    export_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    audit_report: Mapped["AuditReport | None"] = relationship(
        "AuditReport", back_populates="job", uselist=False
    )
