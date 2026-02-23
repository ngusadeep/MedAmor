"""EHR input and mock API schemas."""

from pydantic import BaseModel


class ExportType:
    """EHR export type (matches sample filenames)."""

    FULL = "full"
    HANDOFF_COMPLETE = "handoff_complete"
    HANDOFF_MINIMAL = "handoff_minimal"
    IMAGING_COMPLETE = "imaging_complete"
    IMAGING_MINIMAL = "imaging_minimal"


class EHRPatientSummary(BaseModel):
    """Summary of one patient's EHR available in mock (list)."""

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
    """Patient bundle for audit: EHR text + optional image refs."""

    patient_id: str
    export_type: str = "full"
    ehr_text: str
    image_refs: list[str] | None = None
