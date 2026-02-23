"""Service layer for patient database operations."""

import json

from sqlalchemy.orm import Session

from .models import Patient
from ..schemas.patient import EHRPatientBundle, EHRPatientDetail, EHRPatientSummary


def get_all_patients(db: Session) -> list[EHRPatientSummary]:
    patients = db.query(Patient).order_by(Patient.patient_name).all()
    return [
        EHRPatientSummary(
            patient_id=p.patient_id,
            patient_name=p.patient_name,
            export_types=["full"],
        )
        for p in patients
    ]


def get_patient_detail(db: Session, patient_id: str) -> EHRPatientDetail | None:
    p = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not p:
        return None
    return EHRPatientDetail(
        patient_id=p.patient_id,
        patient_name=p.patient_name,
        birth_date=p.birth_date,
        gender=p.gender,
        address=p.address,
        phone=p.phone,
        race=p.race,
        ethnicity=p.ethnicity,
        marital_status=p.marital_status,
        timeline_ready=p.timeline_cache is not None,
    )


def get_patient_bundle(db: Session, patient_id: str) -> EHRPatientBundle | None:
    """Return timeline text, generating and caching it from FHIR JSON if needed."""
    p = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not p:
        return None

    if p.timeline_cache is None and p.fhir_json:
        p.timeline_cache = _generate_timeline(p.fhir_json)
        db.commit()

    timeline = p.timeline_cache or ""
    return EHRPatientBundle(
        patient_id=p.patient_id,
        export_type="full",
        ehr_text=timeline,
        image_refs=None,
    )


def create_patient(
    db: Session,
    *,
    patient_id: str,
    patient_name: str | None,
    birth_date: str | None = None,
    gender: str | None = None,
    address: str | None = None,
    phone: str | None = None,
    race: str | None = None,
    ethnicity: str | None = None,
    marital_status: str | None = None,
    fhir_json: str | None = None,
) -> Patient:
    patient = Patient(
        patient_id=patient_id,
        patient_name=patient_name,
        birth_date=birth_date,
        gender=gender,
        address=address,
        phone=phone,
        race=race,
        ethnicity=ethnicity,
        marital_status=marital_status,
        fhir_json=fhir_json,
        timeline_cache=None,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _generate_timeline(fhir_json_str: str) -> str:
    from ehr.fhir_reader.timeline import FHIRTimelineConverter

    bundle = json.loads(fhir_json_str)
    return FHIRTimelineConverter(bundle).convert(include_costs=True, include_codes=False)
