"""Jobs API: create and list audit jobs."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.deps import get_current_user_required
from app.models.job import AUDIT_TYPE_DEFAULT, Job, JobStatus
from app.models.user import User
from app.schemas.job import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse)
def create_job(
    body: JobCreate,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> Job:
    """Create an audit job (pending). Celery processes it; default audit type is breast cancer screening."""
    job = Job(
        patient_id=body.patient_id,
        audit_type=body.audit_type or AUDIT_TYPE_DEFAULT,
        status=JobStatus.PENDING,
        export_type=body.export_type,
        triggered_by=body.triggered_by,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    from app.worker.tasks import run_audit_task
    run_audit_task.delay(str(job.id))
    return job


@router.get("", response_model=list[JobResponse])
def list_jobs(
    patient_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
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
    _user: User = Depends(get_current_user_required),
) -> Job:
    """Get one job by id."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
