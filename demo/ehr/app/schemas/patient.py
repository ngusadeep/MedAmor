"""Pydantic schemas for EHR patient data."""

from pydantic import BaseModel


class EHRPatientSummary(BaseModel):
    """Summary of one patient's EHR available in the service."""

    patient_id: str
    patient_name: str | None = None
    export_types: list[str]


class EHRPatientBundle(BaseModel):
    """Patient bundle for audit: EHR text + optional image refs."""

    patient_id: str
    export_type: str = "full"
    ehr_text: str
    image_refs: list[str] | None = None