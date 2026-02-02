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


class EHRPatientBundle(BaseModel):
    """Patient bundle for audit: EHR text + optional image refs."""

    patient_id: str
    export_type: str = "full"
    ehr_text: str
    image_refs: list[str] | None = None
