"""Audit report request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FindingItem(BaseModel):
    """Single finding in an audit report."""

    category: str
    description: str
    responsible_doctor: str | None = None
    urgency: str | None = None


class EvidenceItem(BaseModel):
    """Single evidence snippet."""

    kb_source: str | None = None
    ehr_snippet: str | None = None
    image_ref: str | None = None


class OrchestratorEvidenceItem(BaseModel):
    """Evidence item from aiorchestrator-style reports."""

    guideline: str
    violation: str


class AuditReportCreate(BaseModel):
    """Payload to store an audit result (from audit engine)."""

    job_id: UUID
    patient_id: str
    status: str  # NO_FINDINGS | FINDING_PRESENT
    risk_level: str | None = None
    executive_summary: str | None = None
    findings: list[FindingItem] | None = None
    evidence: list[EvidenceItem] | None = None
    corrective_actions: list[str] | None = None
    next_audit_date: datetime | None = None
    created_at: datetime | None = None  # override creation timestamp (e.g. for seeding)


class OrchestratorAuditReport(BaseModel):
    """aiorchestrator-style audit report structure."""

    compliant: bool
    gaps: list[str] = []
    evidence: list[OrchestratorEvidenceItem] = []


class AuditReportResponse(BaseModel):
    """Audit report in API response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    patient_id: str
    status: str
    risk_level: str | None
    executive_summary: str | None
    findings: list | None
    evidence: list | None
    corrective_actions: list | None
    next_audit_date: datetime | None
    created_at: datetime


class ReportAnnotationCreate(BaseModel):
    """Add a reviewer note to a finding."""

    finding_index: int
    note: str


class ReportAnnotationResponse(BaseModel):
    """Annotation in API response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_report_id: UUID
    finding_index: int
    note: str
    created_by_user_id: UUID | None
    created_at: datetime


class AuditReportExportRow(BaseModel):
    """One row for Kaggle / evaluation export (flat, submission-friendly)."""

    id: str
    job_id: str
    patient_id: str
    status: str
    risk_level: str | None
    executive_summary: str | None
    findings_json: str | None
    evidence_json: str | None
    corrective_actions_json: str | None
    next_audit_date: datetime | None
    created_at: datetime
