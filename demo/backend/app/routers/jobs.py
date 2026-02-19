"""Jobs API: create (single or batch) and list audit jobs."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.deps import get_current_chief_doctor_required
from app.models.job import AUDIT_TYPE_DEFAULT, Job, JobStatus
from app.models.user import User
from app.schemas.job import JobCreate, JobCreateBatch, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _create_one_job(
    db: Session,
    patient_id: str,
    audit_type: str | None = None,
    export_type: str | None = None,
    triggered_by: str | None = None,
    skip_celery: bool = False,
    created_at: datetime | None = None,
) -> Job:
    now = created_at or datetime.utcnow()
    job = Job(
        patient_id=patient_id,
        audit_type=audit_type or AUDIT_TYPE_DEFAULT,
        status=JobStatus.COMPLETED if skip_celery else JobStatus.PENDING,
        export_type=export_type,
        triggered_by=triggered_by,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.post("", response_model=JobResponse)
def create_job(
    body: JobCreate,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_chief_doctor_required),
) -> Job:
    """Create one audit job. Pass skip_celery=true to mark it completed without queuing."""
    job = _create_one_job(
        db,
        body.patient_id,
        audit_type=body.audit_type,
        export_type=body.export_type,
        triggered_by=body.triggered_by,
        skip_celery=body.skip_celery,
        created_at=body.created_at,
    )
    if not body.skip_celery:
        from app.worker.tasks import run_audit_task
        run_audit_task.delay(str(job.id))
    return job


@router.post("/batch", response_model=list[JobResponse])
def create_jobs_batch(
    body: JobCreateBatch,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_chief_doctor_required),
) -> list[Job]:
    """Create one audit job per patient_id. Each job is queued for processing."""
    if not body.patient_ids:
        raise HTTPException(status_code=400, detail="patient_ids must not be empty")
    from app.worker.tasks import run_audit_task

    jobs: list[Job] = []
    for pid in body.patient_ids:
        pid_clean = (pid or "").strip()
        if not pid_clean:
            continue
        job = _create_one_job(
            db,
            pid_clean,
            audit_type=body.audit_type,
            export_type=body.export_type,
            triggered_by=body.triggered_by,
        )
        jobs.append(job)
        run_audit_task.delay(str(job.id))
    return jobs


@router.get("", response_model=list[JobResponse])
def list_jobs(
    patient_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_chief_doctor_required),
) -> list[Job]:
    """List jobs; optional filter by patient_id or status."""
    q = db.query(Job)
    if patient_id:
        q = q.filter(Job.patient_id == patient_id)
    if status:
        q = q.filter(Job.status == status)
    q = q.order_by(Job.created_at.desc())
    return list(q.all())


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_chief_doctor_required),
) -> Job:
    """Get one job by id."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/task/{task_id}/status")
def get_task_status(
    task_id: str,
    _user: User = Depends(get_current_chief_doctor_required),
) -> dict:
    """Get status of a Celery task."""
    try:
        from app.worker.celery_app import celery_app
        from celery.result import AsyncResult

        task = AsyncResult(task_id, app=celery_app)

        if task.state == "PENDING":
            response = {
                "status": "pending",
                "state": "PENDING",
                "task_id": task_id,
                "message": "Task is waiting in queue",
            }
        elif task.state == "PROCESSING":
            response = {
                "status": "processing",
                "state": "PROCESSING",
                "task_id": task_id,
                "message": "Task is being processed",
                "meta": task.info,  # Progress info
            }
        elif task.state == "SUCCESS":
            result = task.result
            response = {
                "status": "completed",
                "state": "SUCCESS",
                "task_id": task_id,
                "result": result,
            }
        elif task.state == "FAILURE":
            response = {
                "status": "failed",
                "state": "FAILURE",
                "task_id": task_id,
                "message": str(task.info),  # Exception info
            }
        else:
            response = {
                "status": task.state.lower(),
                "state": task.state,
                "task_id": task_id,
                "message": f"Task is in state: {task.state}",
            }

        return response

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get task status: {str(e)}",
        }


@router.get("/queue/stats")
def get_queue_stats(
    _user: User = Depends(get_current_chief_doctor_required),
) -> dict:
    """Get queue statistics and worker status."""
    try:
        from app.worker.celery_app import celery_app

        # Get Celery inspector
        inspect = celery_app.control.inspect()

        # Get active tasks
        active = inspect.active()
        reserved = inspect.reserved()
        stats = inspect.stats()

        active_count = sum(len(tasks) for tasks in (active or {}).values())
        reserved_count = sum(len(tasks) for tasks in (reserved or {}).values())
        workers = list((stats or {}).keys())

        return {
            "workers": {
                "count": len(workers),
                "names": workers,
            },
            "queue": {
                "active_jobs": active_count,
                "queued_jobs": reserved_count,
            },
            "details": {
                "active_tasks": active,
                "reserved_tasks": reserved,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get queue stats: {str(e)}",
        }
