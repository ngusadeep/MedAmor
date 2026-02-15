"""Patient management API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.deps import get_current_user_required
from app.models.patient import Patient, PatientStatus
from app.models.user import User
from app.schemas.patient import PatientResponse, PatientStats
from app.services.patient_sync import (
    sync_patients_from_ehr,
    update_patient_status_from_reports,
    get_patients_due_for_review
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=List[PatientResponse])
def list_patients(
    status: str | None = None,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required)
) -> List[PatientResponse]:
    """List all patients with optional status filter."""
    query = db.query(Patient).filter(Patient.is_active == True)

    if status:
        query = query.filter(Patient.status == status)

    patients = query.order_by(Patient.patient_name).all()
    return [
        PatientResponse(
            id=str(p.id),
            patient_id=p.patient_id,
            patient_name=p.patient_name,
            status=p.status,
            last_audit_date=p.last_audit_date,
            next_audit_date=p.next_audit_date,
            risk_level=p.risk_level,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in patients
    ]


@router.get("/stats", response_model=PatientStats)
def get_patient_stats(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required)
) -> PatientStats:
    """Get patient statistics for dashboard."""
    total_patients = db.query(Patient).filter(Patient.is_active == True).count()

    status_counts = {}
    for status in [
        PatientStatus.NEVER_AUDITED,
        PatientStatus.DUE_FOR_REVIEW,
        PatientStatus.RECENTLY_AUDITED,
        PatientStatus.COMPLIANT,
        PatientStatus.NEEDS_ATTENTION
    ]:
        status_counts[status] = db.query(Patient).filter(
            Patient.is_active == True,
            Patient.status == status
        ).count()

    due_patients = get_patients_due_for_review(db)
    due_count = len(due_patients)

    return PatientStats(
        total_patients=total_patients,
        status_counts=status_counts,
        due_for_review_count=due_count
    )


@router.post("/sync")
async def sync_patients(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required)
):
    """Trigger async sync of patient data from EHR service."""
    background_tasks.add_task(sync_patients_from_ehr, db)
    return {"message": "Patient sync started in background"}


@router.post("/update-status")
def update_patient_status(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required)
):
    """Update patient status based on latest audit reports."""
    result = update_patient_status_from_reports(db)
    return result


@router.get("/due-for-review", response_model=List[PatientResponse])
def list_patients_due_for_review(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required)
) -> List[PatientResponse]:
    """Get patients who are due for review."""
    patients = get_patients_due_for_review(db)
    return [
        PatientResponse(
            id=str(p.id),
            patient_id=p.patient_id,
            patient_name=p.patient_name,
            status=p.status,
            last_audit_date=p.last_audit_date,
            next_audit_date=p.next_audit_date,
            risk_level=p.risk_level,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in patients
    ]