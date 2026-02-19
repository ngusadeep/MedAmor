"""Job request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobStatusEnum:
    """Job status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Request body to create an audit job (Breast Cancer Screening)."""

    patient_id: str
    audit_type: str | None = None  # default breast_cancer_screening
    export_type: str | None = None
    triggered_by: str | None = None


class JobResponse(BaseModel):
    """Job in API response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: str
    audit_type: str
    status: str
    triggered_by: str | None
    export_type: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class JobCreateBatch(BaseModel):
    """Request body to create multiple audit jobs (one per patient)."""

    patient_ids: list[str]
    audit_type: str | None = None
    export_type: str | None = None
    triggered_by: str | None = None
