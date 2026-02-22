"""Patient API schemas."""

from datetime import datetime
from typing import Dict
from pydantic import BaseModel


class PatientResponse(BaseModel):
    """Patient data response."""

    id: str
    patient_id: str
    patient_name: str | None
    status: str
    last_audit_date: datetime | None
    next_audit_date: datetime | None
    risk_level: str | None
    created_at: datetime
    updated_at: datetime


class PatientStats(BaseModel):
    """Patient statistics for dashboard."""

    total_patients: int
    status_counts: Dict[str, int]
    due_for_review_count: int
