"""Patient API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.patient_service import get_all_patients, get_patient_bundle
from ..schemas.patient import EHRPatientSummary, EHRPatientBundle

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=list[EHRPatientSummary])
def list_patients(db: Session = Depends(get_db)) -> list[EHRPatientSummary]:
    """List all patients."""
    return get_all_patients(db)


@router.get("/{patient_id}", response_model=EHRPatientBundle)
def get_patient(
    patient_id: str,
    export_type: str = "full",
    db: Session = Depends(get_db)
) -> EHRPatientBundle:
    """Get patient bundle by patient_id."""
    if export_type != "full":
        raise HTTPException(
            status_code=400,
            detail="Only 'full' export_type is currently supported"
        )

    bundle = get_patient_bundle(db, patient_id)
    if not bundle:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with id {patient_id} not found"
        )

    return bundle