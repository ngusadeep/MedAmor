"""Service layer for patient database operations."""

from sqlalchemy.orm import Session

from .models import Patient
from ..schemas.patient import EHRPatientSummary, EHRPatientBundle


def get_all_patients(db: Session) -> list[EHRPatientSummary]:
    """Get all patients from database."""
    patients = db.query(Patient).all()
    return [
        EHRPatientSummary(
            patient_id=patient.patient_id,
            patient_name=patient.patient_name,
            export_types=["full"]  # For now, only support "full" export type
        )
        for patient in patients
    ]


def get_patient_bundle(db: Session, patient_id: str) -> EHRPatientBundle | None:
    """Get patient bundle by patient_id."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return None

    return EHRPatientBundle(
        patient_id=patient.patient_id,
        export_type="full",
        ehr_text=patient.ehr_text,
        image_refs=None
    )


def create_patient(db: Session, patient_id: str, patient_name: str | None, ehr_text: str) -> Patient:
    """Create a new patient record."""
    patient = Patient(
        patient_id=patient_id,
        patient_name=patient_name,
        ehr_text=ehr_text
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient