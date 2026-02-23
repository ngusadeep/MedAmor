"""Pydantic schemas for EHR patient data."""

from pydantic import BaseModel


class EHRPatientSummary(BaseModel):
    """Patient list item — name + available export types."""

    patient_id: str
    patient_name: str | None = None
    export_types: list[str]


class EHRPatientDetail(BaseModel):
    """Rich patient demographics for the patient detail view."""

    patient_id: str
    patient_name: str | None = None
    birth_date: str | None = None
    gender: str | None = None
    address: str | None = None
    phone: str | None = None
    race: str | None = None
    ethnicity: str | None = None
    marital_status: str | None = None
    timeline_ready: bool = False


class EHRPatientBundle(BaseModel):
    """Patient bundle for audit: timeline text + optional image refs."""

    patient_id: str
    export_type: str = "full"
    ehr_text: str
    image_refs: list[str] | None = None
