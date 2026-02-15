"""Celery tasks: run audit job; create scheduled jobs (CRON)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.audit_report import AuditReport
from app.models.job import Job, JobStatus
from app.services.audit_engine import run_audit
from app.services.ehr_mock import list_patients
from app.worker.celery_app import celery_app


@celery_app.task(bind=True, name="app.worker.tasks.run_audit_task")
def run_audit_task(self, job_id: str):
    """Load job, run audit (EHR + RAG + MedGemma), save report, update job status."""
    db: Session = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == UUID(job_id)).first()
        if not job:
            return {"ok": False, "error": "Job not found"}
        if job.status != JobStatus.PENDING:
            return {"ok": False, "error": f"Job not pending: {job.status}"}

        job.status = JobStatus.IN_PROGRESS
        db.commit()

        report_create = run_audit(
            job.id, job.patient_id, job.export_type, getattr(job, "audit_type", None)
        )

        report = AuditReport(
            job_id=report_create.job_id,
            patient_id=report_create.patient_id,
            status=report_create.status,
            risk_level=report_create.risk_level,
            executive_summary=report_create.executive_summary,
            findings=[f.model_dump() for f in (report_create.findings or [])],
            evidence=[e.model_dump() for e in (report_create.evidence or [])],
            corrective_actions=report_create.corrective_actions,
            next_audit_date=report_create.next_audit_date,
        )
        db.add(report)
        job.status = JobStatus.COMPLETED
        job.error_message = None
        db.commit()
        return {"ok": True, "report_id": str(report.id)}
    except Exception as e:
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)[:500]
            db.commit()
        raise
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.create_scheduled_audit_jobs")
def create_scheduled_audit_jobs():
    """
    CRON: create audit jobs for patients due for review (next_audit_date <= today)
    or never audited. No medical logic—only decides who to queue.
    """
    from app.models.job import AUDIT_TYPE_DEFAULT

    db = SessionLocal()
    try:
        today = datetime.now(timezone.utc).date()
        # Latest report per patient (by created_at)
        reports = (
            db.query(AuditReport)
            .order_by(AuditReport.patient_id, AuditReport.created_at.desc())
            .all()
        )
        latest_by_patient: dict[str, AuditReport] = {}
        for r in reports:
            if r.patient_id not in latest_by_patient:
                latest_by_patient[r.patient_id] = r
        due_patient_ids = [
            pid
            for pid, r in latest_by_patient.items()
            if r.next_audit_date is not None
            and r.next_audit_date.date() <= today
        ]
        all_patients = {p.patient_id for p in list_patients()}
        audited = set(latest_by_patient.keys())
        never_audited = list(all_patients - audited)
        to_queue = list(dict.fromkeys(due_patient_ids + never_audited))
        created = 0
        for patient_id in to_queue:
            existing = (
                db.query(Job)
                .filter(Job.patient_id == patient_id, Job.status == JobStatus.PENDING)
                .first()
            )
            if existing:
                continue
            job = Job(
                patient_id=patient_id,
                audit_type=AUDIT_TYPE_DEFAULT,
                status=JobStatus.PENDING,
                triggered_by="scheduled",
            )
            db.add(job)
            db.commit()
            run_audit_task.delay(str(job.id))
            created += 1
        return {"ok": True, "jobs_created": created, "due": len(due_patient_ids), "never_audited": len(never_audited)}
    finally:
        db.close()
