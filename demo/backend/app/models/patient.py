"""Patient model for storing patient data from EHR service."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.audit_report import AuditReport


class PatientStatus:
    """Patient review status constants."""

    NEVER_AUDITED = "never_audited"
    DUE_FOR_REVIEW = "due_for_review"
    RECENTLY_AUDITED = "recently_audited"
    COMPLIANT = "compliant"
    NEEDS_ATTENTION = "needs_attention"


class Patient(Base):
    """Patient data synced from EHR service with audit tracking."""

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    patient_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ehr_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit tracking
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=PatientStatus.NEVER_AUDITED, index=True
    )
    last_audit_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_audit_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


    def __repr__(self):
        return f"<Patient(patient_id={self.patient_id}, status={self.status})>"