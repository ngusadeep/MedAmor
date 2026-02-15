"""HTTP client for EHR FastAPI service. Used by backend when EHR_SERVICE_URL is set."""

import httpx

from app.schemas.ehr import EHRPatientBundle, EHRPatientSummary


def list_patients_from_service(base_url: str) -> list[EHRPatientSummary]:
    """GET {base_url}/patients -> list[EHRPatientSummary]."""
    url = base_url.rstrip("/") + "/patients/"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
    return [EHRPatientSummary.model_validate(item) for item in data]


def get_patient_bundle_from_service(
    base_url: str, patient_id: str, export_type: str = "full"
) -> EHRPatientBundle | None:
    """GET {base_url}/patients/{patient_id}?export_type=... -> EHRPatientBundle or None if 404."""
    url = f"{base_url.rstrip('/')}/patients/{patient_id}/"
    with httpx.Client(timeout=60.0) as client:
        r = client.get(url, params={"export_type": export_type})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return EHRPatientBundle.model_validate(r.json())
