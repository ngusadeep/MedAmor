"""Audit reports API: list and get audit results."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.audit_report import AuditReport
from app.schemas.audit_report import AuditReportResponse

router = APIRouter(prefix="/audit-reports", tags=["audit-reports"])


@router.get("", response_model=list[AuditReportResponse])
def list_audit_reports(
    job_id: UUID | None = None,
    patient_id: str | None = None,
    db: Session = Depends(get_db_session),
) -> list[AuditReport]:
    """List audit reports; optional filter by job_id or patient_id."""
    q = db.query(AuditReport)
    if job_id:
        q = q.filter(AuditReport.job_id == job_id)
    if patient_id:
        q = q.filter(AuditReport.patient_id == patient_id)
    q = q.order_by(AuditReport.created_at.desc())
    return list(q.all())


@router.get("/{report_id}", response_model=AuditReportResponse)
def get_audit_report(
    report_id: UUID, db: Session = Depends(get_db_session)
) -> AuditReport:
    """Get one audit report by id."""
    report = db.query(AuditReport).filter(AuditReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")
    return report


@router.get("/by-job/{job_id}", response_model=AuditReportResponse | None)
def get_audit_report_by_job(
    job_id: UUID, db: Session = Depends(get_db_session)
) -> AuditReport | None:
    """Get audit report for a job (if completed)."""
    report = (
        db.query(AuditReport).filter(AuditReport.job_id == job_id).first()
    )
    return report
