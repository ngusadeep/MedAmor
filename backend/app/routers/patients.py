"""Patient management API endpoints - fetches from EHR service, enriched with audit data."""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.deps import get_current_user_required
from app.models.user import User
from app.schemas.patient import PatientResponse, PatientStats
from app.services.ehr_mock import list_patients as list_ehr_patients
from app.services.patient_enrichment import (
    derive_patient_status,
    get_latest_report_per_patient,
    get_patients_due_for_review_ids,
)

router = APIRouter(prefix="/patients", tags=["patients"])


def _enrich_patients(db: Session, ehr_patients: list, latest_map: dict) -> List[PatientResponse]:
    now = datetime.now(timezone.utc)
    out = []
    for p in ehr_patients:
        info = latest_map.get(p.patient_id)
        if info:
            last_d = info.get("last_audit_date")
            next_d = info.get("next_audit_date")
            risk = info.get("risk_level")
            report_status = info.get("report_status")
            status = derive_patient_status(last_d, next_d, report_status, risk)
        else:
            last_d = next_d = risk = None
            status = "never_audited"
        out.append(
            PatientResponse(
                id=p.patient_id,
                patient_id=p.patient_id,
                patient_name=p.patient_name,
                status=status,
                last_audit_date=last_d,
                next_audit_date=next_d,
                risk_level=risk,
                created_at=now,
                updated_at=now,
            )
        )
    return out


@router.get("/", response_model=List[PatientResponse])
def get_patients(
    status: str | None = None,
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> List[PatientResponse]:
    """List all patients from EHR service, enriched with last/next audit date and status."""
    ehr_patients = list_ehr_patients()
    latest_map = get_latest_report_per_patient(db)
    result = _enrich_patients(db, ehr_patients, latest_map)
    if status:
        result = [r for r in result if r.status == status]
    return result


@router.get("/stats", response_model=PatientStats)
def get_patient_stats(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> PatientStats:
    """Patient statistics: total, due_for_review, and counts by status."""
    ehr_patients = list_ehr_patients()
    latest_map = get_latest_report_per_patient(db)
    enriched = _enrich_patients(db, ehr_patients, latest_map)

    status_counts = {
        "never_audited": 0,
        "due_for_review": 0,
        "recently_audited": 0,
        "compliant": 0,
        "needs_attention": 0,
    }
    for r in enriched:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1

    due_count = len(
        get_patients_due_for_review_ids(db, [p.patient_id for p in ehr_patients])
    )

    return PatientStats(
        total_patients=len(ehr_patients),
        status_counts=status_counts,
        due_for_review_count=due_count,
    )


@router.post("/sync")
def sync_patients(_user: User = Depends(get_current_user_required)):
    """Trigger patient sync from EHR service (no-op; data fetched on-demand)."""
    return {"message": "Patient sync completed", "status": "success"}


@router.post("/update-status")
def update_patient_status(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
):
    """Status is computed from latest report on read; no persistent update. Returns count for UI."""
    return {"updated_patients": 0}


@router.get("/due-for-review", response_model=List[PatientResponse])
def list_patients_due_for_review(
    db: Session = Depends(get_db_session),
    _user: User = Depends(get_current_user_required),
) -> List[PatientResponse]:
    """Patients due for review (next_audit_date <= today or never audited), no pending job."""
    ehr_patients = list_ehr_patients()
    due_ids = get_patients_due_for_review_ids(db, [p.patient_id for p in ehr_patients])
    due_set = set(due_ids)
    filtered = [p for p in ehr_patients if p.patient_id in due_set]
    latest_map = get_latest_report_per_patient(db)
    result = _enrich_patients(db, filtered, latest_map)
    # Normalize status for due-for-review list
    now = datetime.now(timezone.utc)
    return [
        PatientResponse(
            id=r.id,
            patient_id=r.patient_id,
            patient_name=r.patient_name,
            status="due_for_review" if r.status in ("due_for_review", "never_audited") else r.status,
            last_audit_date=r.last_audit_date,
            next_audit_date=r.next_audit_date,
            risk_level=r.risk_level,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in result
    ]
