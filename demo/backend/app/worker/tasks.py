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
        error_msg = f"Audit failed for patient {job.patient_id if job else 'unknown'}: {str(e)}"
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
    CRON: create audit jobs for all patients from EHR service.
    Simplified version: create jobs for all patients that don't have pending jobs.
    """
    from app.models.job import AUDIT_TYPE_DEFAULT, JobStatus

    db = SessionLocal()
    try:
        # Get all patients from EHR service
        from app.services.ehr_mock import list_patients
        all_patients = list_patients()

        created = 0
        for patient in all_patients:
            # Check if there's already a pending or in-progress job for this patient
            existing = (
                db.query(Job)
                .filter(
                    Job.patient_id == patient.patient_id,
                    Job.status.in_([JobStatus.PENDING, JobStatus.IN_PROGRESS])
                )
                .first()
            )
            if existing:
                continue

            job = Job(
                patient_id=patient.patient_id,
                audit_type=AUDIT_TYPE_DEFAULT,
                status=JobStatus.PENDING,
                triggered_by="scheduled",
            )
            db.add(job)
            db.commit()
            run_audit_task.delay(str(job.id))
            created += 1

        return {
            "ok": True,
            "jobs_created": created,
            "total_patients": len(all_patients)
        }
    finally:
        db.close()
