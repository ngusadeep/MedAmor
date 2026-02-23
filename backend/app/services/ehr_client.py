"""HTTP client for EHR FastAPI service. Used by backend when EHR_SERVICE_URL is set."""

import httpx

from app.schemas.ehr import EHRPatientBundle, EHRPatientDetail, EHRPatientSummary


def list_patients_from_service(base_url: str) -> list[EHRPatientSummary]:
    url = base_url.rstrip("/") + "/patients/"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url)
        r.raise_for_status()
    return [EHRPatientSummary.model_validate(item) for item in r.json()]


def get_patient_detail_from_service(
    base_url: str, patient_id: str
) -> EHRPatientDetail | None:
    url = f"{base_url.rstrip('/')}/patients/{patient_id}/detail"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
    return EHRPatientDetail.model_validate(r.json())


def get_patient_bundle_from_service(
    base_url: str, patient_id: str, export_type: str = "full"
) -> EHRPatientBundle | None:
    # No trailing slash — avoids a 307 redirect
    url = f"{base_url.rstrip('/')}/patients/{patient_id}"
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url, params={"export_type": export_type})
        if r.status_code == 404:
            return None
        r.raise_for_status()
    return EHRPatientBundle.model_validate(r.json())
