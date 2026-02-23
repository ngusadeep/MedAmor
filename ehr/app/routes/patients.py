"""Patient API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.patient_service import get_all_patients, get_patient_bundle, get_patient_detail
from ..schemas.patient import EHRPatientBundle, EHRPatientDetail, EHRPatientSummary

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=list[EHRPatientSummary])
def list_patients(db: Session = Depends(get_db)) -> list[EHRPatientSummary]:
    """List all patients (name + ID)."""
    return get_all_patients(db)


@router.get("/{patient_id}/detail", response_model=EHRPatientDetail)
def get_patient_detail_route(
    patient_id: str, db: Session = Depends(get_db)
) -> EHRPatientDetail:
    """Return rich demographics for a patient (no timeline generation)."""
    detail = get_patient_detail(db, patient_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return detail


@router.get("/{patient_id}", response_model=EHRPatientBundle)
def get_patient_bundle_route(
    patient_id: str,
    export_type: str = "full",
    db: Session = Depends(get_db),
) -> EHRPatientBundle:
    """Return the patient's timeline text, generating and caching it from FHIR if needed."""
    if export_type != "full":
        raise HTTPException(status_code=400, detail="Only 'full' export_type is supported")
    bundle = get_patient_bundle(db, patient_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return bundle
