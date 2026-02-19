"""Enrich patient list with last/next audit dates and status from latest report."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_report import AuditReport


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_latest_report_per_patient(db: Session) -> dict[str, dict[str, Any]]:
    """
    Return map: patient_id -> { last_audit_date, next_audit_date, risk_level, report_status }.
    Uses the latest report (by created_at) per patient.
    """
    reports = (
        db.query(AuditReport)
        .order_by(AuditReport.patient_id, AuditReport.created_at.desc())
        .all()
    )
    out: dict[str, dict[str, Any]] = {}
    for r in reports:
        if r.patient_id in out:
            continue
        out[r.patient_id] = {
            "last_audit_date": _ensure_utc(r.created_at),
            "next_audit_date": _ensure_utc(r.next_audit_date),
            "risk_level": r.risk_level,
            "report_status": r.status,
        }
    return out


def derive_patient_status(
    last_audit_date: datetime | None,
    next_audit_date: datetime | None,
    report_status: str | None,
    risk_level: str | None,
) -> str:
    """
    Derive display status: never_audited, due_for_review, needs_attention, compliant, recently_audited.
    """
    now = _utc_now()
    has_report = last_audit_date is not None

    if not has_report:
        return "never_audited"

    is_due = next_audit_date is None or next_audit_date <= now
    has_findings = report_status == "FINDING_PRESENT"
    high_risk = (risk_level or "").lower() == "high"

    if has_findings or high_risk:
        return "needs_attention"
    if is_due:
        return "due_for_review"
    if report_status == "NO_FINDINGS" and next_audit_date and next_audit_date > now:
        return "compliant"
    return "recently_audited"


def get_patients_due_for_review_ids(db: Session, ehr_patient_ids: list[str]) -> list[str]:
    """
    Return EHR patient IDs that are due for review:
    - no report yet, or
    - latest report has next_audit_date is None or next_audit_date <= today.
    Excludes patients that already have a PENDING or IN_PROGRESS job.
    """
    from app.models.job import Job, JobStatus

    latest = get_latest_report_per_patient(db)
    now = _utc_now().date()

    due_ids = []
    for pid in ehr_patient_ids:
        info = latest.get(pid)
        if info is None:
            due_ids.append(pid)
            continue
        next_d = info.get("next_audit_date")
        if next_d is None:
            due_ids.append(pid)
            continue
        next_date = next_d.date() if hasattr(next_d, "date") else next_d
        if next_date <= now:
            due_ids.append(pid)

    # Exclude patients with existing PENDING or IN_PROGRESS job
    existing = (
        db.query(Job.patient_id)
        .filter(
            Job.patient_id.in_(due_ids),
            Job.status.in_([JobStatus.PENDING, JobStatus.IN_PROGRESS]),
        )
        .distinct()
        .all()
    )
    busy = {r[0] for r in existing}
    return [pid for pid in due_ids if pid not in busy]
