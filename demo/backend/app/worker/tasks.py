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
    """Load job, run audit using LangGraph orchestrator, save report, update job status."""
    db: Session = SessionLocal()
    job = None
    try:
        job = db.query(Job).filter(Job.id == UUID(job_id)).first()
        if not job:
            return {"ok": False, "error": "Job not found"}
        if job.status != JobStatus.PENDING:
            return {"ok": False, "error": f"Job not pending: {job.status}"}

        # Update task state to show progress
        self.update_state(
            state="PROCESSING",
            meta={
                "patient_id": job.patient_id,
                "audit_type": getattr(job, "audit_type", "general"),
                "stage": "Initializing audit workflow",
            },
        )

        job.status = JobStatus.IN_PROGRESS
        db.commit()

        # Update progress: Fetching EHR data
        self.update_state(
            state="PROCESSING",
            meta={
                "patient_id": job.patient_id,
                "audit_type": getattr(job, "audit_type", "general"),
                "stage": "Fetching patient EHR data",
            },
        )

        report_create = run_audit(
            job.id, job.patient_id, job.export_type, getattr(job, "audit_type", None)
        )

        # Update progress: Processing complete
        self.update_state(
            state="PROCESSING",
            meta={
                "patient_id": job.patient_id,
                "audit_type": getattr(job, "audit_type", "general"),
                "stage": "Audit analysis complete",
            },
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
        error_msg = (
            f"Audit failed for patient {job.patient_id if job else 'unknown'}: {str(e)}"
        )
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
    CRON (e.g. every 24h): create one audit job per patient due for review.
    Due = no report yet, or latest report's next_audit_date <= today.
    Skips patients that already have a PENDING or IN_PROGRESS job.
    Each job runs full RAG/agentic workflow (run_audit_task -> orchestrator -> report with next_audit_date).
    """
    from app.models.job import AUDIT_TYPE_DEFAULT, JobStatus
    from app.services.ehr_mock import list_patients
    from app.services.patient_enrichment import get_patients_due_for_review_ids

    db = SessionLocal()
    try:
        all_patients = list_patients()
        ehr_ids = [p.patient_id for p in all_patients]
        due_ids = get_patients_due_for_review_ids(db, ehr_ids)

        created = 0
        for patient_id in due_ids:
            job = Job(
                patient_id=patient_id,
                audit_type=AUDIT_TYPE_DEFAULT,
                status=JobStatus.PENDING,
                triggered_by="scheduled",
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            run_audit_task.delay(str(job.id))
            created += 1

        return {
            "ok": True,
            "jobs_created": created,
            "total_patients": len(all_patients),
            "due_for_review": len(due_ids),
        }
    finally:
        db.close()
