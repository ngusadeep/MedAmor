"""Audit reports API: create, list, get, and human-in-the-loop annotations."""

import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.deps import get_current_user_required
from app.models.audit_report import AuditReport
from app.models.job import Job
from app.models.report_annotation import ReportAnnotation
from app.models.user import User
from app.schemas.audit_report import (
    AuditReportCreate,
    AuditReportExportRow,
    AuditReportResponse,
    ReportAnnotationCreate,
    ReportAnnotationResponse,
)

router = APIRouter(prefix="/audit-reports", tags=["audit-reports"])


@router.post("", response_model=AuditReportResponse)
def create_audit_report(
    body: AuditReportCreate,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> AuditReport:
    """Store a completed audit report for an existing job."""
    job = db.query(Job).filter(Job.id == body.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if db.query(AuditReport).filter(AuditReport.job_id == body.job_id).first():
        raise HTTPException(status_code=409, detail="Audit report already exists for this job")
    now = body.created_at or datetime.utcnow()
    report = AuditReport(
        job_id=body.job_id,
        patient_id=body.patient_id,
        status=body.status,
        risk_level=body.risk_level,
        executive_summary=body.executive_summary,
        findings=[f.model_dump() for f in body.findings] if body.findings else [],
        evidence=[e.model_dump() for e in body.evidence] if body.evidence else [],
        corrective_actions=body.corrective_actions or [],
        next_audit_date=body.next_audit_date,
        created_at=now,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=list[AuditReportResponse])
def list_audit_reports(
    job_id: UUID | None = None,
    patient_id: str | None = None,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
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
    report_id: UUID,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> AuditReport:
    """Get one audit report by id."""
    report = db.query(AuditReport).filter(AuditReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")
    return report


@router.get("/by-job/{job_id}", response_model=AuditReportResponse | None)
def get_audit_report_by_job(
    job_id: UUID,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> AuditReport | None:
    """Get audit report for a job (if completed)."""
    report = db.query(AuditReport).filter(AuditReport.job_id == job_id).first()
    return report


@router.get("/{report_id}/annotations", response_model=list[ReportAnnotationResponse])
def list_report_annotations(
    report_id: UUID,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> list[ReportAnnotation]:
    """List reviewer annotations for a report (human-in-the-loop)."""
    if db.query(AuditReport).filter(AuditReport.id == report_id).first() is None:
        raise HTTPException(status_code=404, detail="Audit report not found")
    return list(
        db.query(ReportAnnotation)
        .filter(ReportAnnotation.audit_report_id == report_id)
        .order_by(ReportAnnotation.finding_index, ReportAnnotation.created_at)
        .all()
    )


@router.post("/{report_id}/annotations", response_model=ReportAnnotationResponse)
def create_report_annotation(
    report_id: UUID,
    body: ReportAnnotationCreate,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user_required),
) -> ReportAnnotation:
    """Add a reviewer note to a finding. Stored separately from AI output."""
    if db.query(AuditReport).filter(AuditReport.id == report_id).first() is None:
        raise HTTPException(status_code=404, detail="Audit report not found")
    ann = ReportAnnotation(
        audit_report_id=report_id,
        finding_index=body.finding_index,
        note=body.note,
        created_by_user_id=user.id,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ann


def _report_to_export_row(report: AuditReport) -> AuditReportExportRow:
    return AuditReportExportRow(
        id=str(report.id),
        job_id=str(report.job_id),
        patient_id=report.patient_id,
        status=report.status,
        risk_level=report.risk_level,
        executive_summary=report.executive_summary,
        findings_json=(
            json.dumps(report.findings) if report.findings is not None else None
        ),
        evidence_json=(
            json.dumps(report.evidence) if report.evidence is not None else None
        ),
        corrective_actions_json=(
            json.dumps(report.corrective_actions)
            if report.corrective_actions is not None
            else None
        ),
        next_audit_date=report.next_audit_date,
        created_at=report.created_at,
    )


@router.get("/export", response_model=list[AuditReportExportRow])
def export_audit_reports(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> list[AuditReportExportRow]:
    """Export all audit reports for Kaggle / evaluation (JSON)."""
    reports = db.query(AuditReport).order_by(AuditReport.created_at.desc()).all()
    return [_report_to_export_row(r) for r in reports]


@router.get("/export/csv")
def export_audit_reports_csv(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> PlainTextResponse:
    """Export all audit reports as CSV for Kaggle / evaluation."""
    import csv
    import io

    reports = db.query(AuditReport).order_by(AuditReport.created_at.desc()).all()
    rows = [_report_to_export_row(r) for r in reports]
    if not rows:
        return PlainTextResponse(
            "id,job_id,patient_id,status,risk_level,executive_summary,findings_json,evidence_json,corrective_actions_json,next_audit_date,created_at\n",
            media_type="text/csv",
        )
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(rows[0].model_dump().keys())
    for row in rows:
        w.writerow(row.model_dump().values())
    return PlainTextResponse(out.getvalue(), media_type="text/csv")
