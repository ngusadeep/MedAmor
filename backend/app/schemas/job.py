"""Job request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobStatusEnum:
    """Job status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Request body to create an audit job."""

    patient_id: str
    export_type: str | None = None
    triggered_by: str | None = None


class JobResponse(BaseModel):
    """Job in API response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: str
    status: str
    triggered_by: str | None
    export_type: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
