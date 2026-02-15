"""Patient management API endpoints - fetches from EHR service."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.deps import get_current_user_required
from app.models.user import User
from app.schemas.patient import PatientResponse, PatientStats
from app.services.ehr_mock import list_patients

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=List[PatientResponse])
def list_patients(
    status: str | None = None,
    _user: User = Depends(get_current_user_required)
) -> List[PatientResponse]:
    """List all patients from EHR service."""
    ehr_patients = list_patients()

    # Filter by status if provided (simplified - in real implementation would track status)
    if status:
        # For now, just return all patients since we don't track status in EHR service
        pass

    return [
        PatientResponse(
            id=p.patient_id,  # Use patient_id as ID since we don't have local IDs
            patient_id=p.patient_id,
            patient_name=p.patient_name,
            status="unknown",  # Simplified - would need to track status separately
            last_audit_date=None,
            next_audit_date=None,
            risk_level=None,
            created_at=None,
            updated_at=None
        )
        for p in ehr_patients
    ]


@router.get("/stats", response_model=PatientStats)
def get_patient_stats(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required)
) -> PatientStats:
    """Get patient statistics for dashboard."""
    from app.models.job import Job, JobStatus
    from app.models.audit_report import AuditReport

    # Get EHR patients
    ehr_patients = list_patients()
    total_patients = len(ehr_patients)

    # Count jobs by status
    pending_jobs = db.query(Job).filter(Job.status == JobStatus.PENDING).count()
    completed_jobs = db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
    failed_jobs = db.query(Job).filter(Job.status == JobStatus.FAILED).count()

    # Count reports with findings
    reports_with_findings = db.query(AuditReport).filter(
        AuditReport.status == "FINDING_PRESENT"
    ).count()

    return PatientStats(
        total_patients=total_patients,
        status_counts={
            "pending_jobs": pending_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "reports_with_findings": reports_with_findings,
        },
        due_for_review_count=pending_jobs  # Simplified
    )


@router.get("/due-for-review", response_model=List[PatientResponse])
def list_patients_due_for_review(
    _user: User = Depends(get_current_user_required)
) -> List[PatientResponse]:
    """Get patients who are due for review (simplified - all patients)."""
    ehr_patients = list_patients()
    return [
        PatientResponse(
            id=p.patient_id,
            patient_id=p.patient_id,
            patient_name=p.patient_name,
            status="due_for_review",
            last_audit_date=None,
            next_audit_date=None,
            risk_level=None,
            created_at=None,
            updated_at=None
        )
        for p in ehr_patients
    ]