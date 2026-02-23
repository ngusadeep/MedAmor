"""Mock EHR API: list patients, get patient detail, and get patient bundle (EHR text)."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user_required
from app.models.user import User
from app.schemas.ehr import EHRPatientBundle, EHRPatientDetail, EHRPatientSummary
from app.services.ehr_mock import get_patient_bundle, get_patient_detail, list_patients

router = APIRouter(prefix="/ehr", tags=["ehr"])


@router.get("/patients", response_model=list[EHRPatientSummary])
def ehr_list_patients(
    _user: User = Depends(get_current_user_required),
) -> list[EHRPatientSummary]:
    """List all patients available in the EHR."""
    return list_patients()


@router.get("/patients/{patient_id}/detail", response_model=EHRPatientDetail)
def ehr_get_patient_detail(
    patient_id: str,
    _user: User = Depends(get_current_user_required),
) -> EHRPatientDetail:
    """Get rich demographics for a patient (DOB, gender, address, etc.)."""
    detail = get_patient_detail(patient_id)
    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {patient_id} not found",
        )
    return detail


@router.get("/patients/{patient_id}", response_model=EHRPatientBundle)
def ehr_get_patient(
    patient_id: str,
    export_type: str = "full",
    _user: User = Depends(get_current_user_required),
) -> EHRPatientBundle:
    """Get the patient's full timeline text for audit (generated and cached on first call)."""
    bundle = get_patient_bundle(patient_id, export_type)
    if not bundle:
        raise HTTPException(
            status_code=404,
            detail=f"EHR not found for patient_id={patient_id}, export_type={export_type}",
        )
    return bundle
