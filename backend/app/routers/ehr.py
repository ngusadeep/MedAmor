"""Mock EHR API: list patients and get patient bundle (EHR text)."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user_required
from app.models.user import User
from app.schemas.ehr import EHRPatientBundle, EHRPatientSummary
from app.services.ehr_mock import get_patient_bundle, list_patients

router = APIRouter(prefix="/ehr", tags=["ehr"])


@router.get("/patients", response_model=list[EHRPatientSummary])
def ehr_list_patients(
    _user: User = Depends(get_current_user_required),
) -> list[EHRPatientSummary]:
    """List patients available in mock EHR (EHR-DATA_* folders)."""
    return list_patients()


@router.get("/patients/{patient_id}", response_model=EHRPatientBundle)
def ehr_get_patient(
    patient_id: str,
    export_type: str = "full",
    _user: User = Depends(get_current_user_required),
) -> EHRPatientBundle:
    """Get one patient's EHR text for the given export_type (full, handoff_complete, etc.)."""
    bundle = get_patient_bundle(patient_id, export_type)
    if not bundle:
        raise HTTPException(
            status_code=404,
            detail=f"EHR not found for patient_id={patient_id}, export_type={export_type}",
        )
    return bundle
