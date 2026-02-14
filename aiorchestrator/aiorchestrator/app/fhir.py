"""FHIR data fetching and formatting utilities."""

from __future__ import annotations

import os
from typing import Any

import requests


HAPI_FHIR_URL = os.environ.get("HAPI_FHIR_URL", "http://localhost:9080/fhir")


def format_patient_summary(fhir_bundle: dict[str, Any]) -> str:
    """Convert FHIR Bundle JSON to a compact narrative string for token efficiency.

    Extracts key clinical information into a readable summary.
    """
    parts: list[str] = []
    entries = fhir_bundle.get("entry", []) or []

    for entry in entries:
        resource = entry.get("resource") if isinstance(entry, dict) else None
        if not resource:
            continue

        rtype = resource.get("resourceType", "")
        rid = resource.get("id", "")

        if rtype == "Patient":
            name_parts = []
            for human_name in resource.get("name", []) or []:
                given = " ".join(human_name.get("given", []) or [])
                family = (human_name.get("family") or "").strip()
                if given or family:
                    name_parts.append(f"{given} {family}".strip())
            name = name_parts[0] if name_parts else rid
            birth = resource.get("birthDate", "N/A")
            gender = resource.get("gender", "unknown")
            parts.append(f"Patient {name} (id={rid}), DOB {birth}, {gender}.")

        elif rtype == "Observation":
            coding = (
                (resource.get("code", {}).get("coding") or [{}])[0]
                if resource.get("code")
                else {}
            )
            display = coding.get("display", coding.get("code", "Observation"))
            value = resource.get("valueQuantity") or resource.get("valueString") or resource.get("valueCode")
            if isinstance(value, dict):
                val_str = value.get("value") or value.get("display", str(value))
            else:
                val_str = str(value) if value is not None else "N/A"
            eff = resource.get("effectiveDateTime", resource.get("effectivePeriod", {}).get("start", "N/A"))
            parts.append(f"Observation: {display} = {val_str} ({eff})")

        elif rtype == "Condition":
            coding = (
                (resource.get("code", {}).get("coding") or [{}])[0]
                if resource.get("code")
                else {}
            )
            display = coding.get("display", coding.get("code", "Condition"))
            onset = resource.get("onsetDateTime", resource.get("onsetPeriod", {}).get("start", "N/A"))
            parts.append(f"Condition: {display} (onset: {onset})")

        elif rtype == "MedicationRequest":
            coding = (
                (resource.get("medicationCodeableConcept", {}).get("coding") or [{}])[0]
                if resource.get("medicationCodeableConcept")
                else {}
            )
            display = coding.get("display", coding.get("code", "Medication"))
            status = resource.get("status", "unknown")
            parts.append(f"MedicationRequest: {display} (status: {status})")

        elif rtype == "Encounter":
            coding = (
                (resource.get("type", [{}])[0].get("coding") or [{}])[0]
                if resource.get("type")
                else {}
            )
            display = coding.get("display", coding.get("code", "Encounter"))
            period = resource.get("period", {})
            start = period.get("start", "N/A")
            parts.append(f"Encounter: {display} ({start})")

        else:
            parts.append(f"{rtype} (id={rid})")

    return " ".join(parts) if parts else "No patient data available."


def fetch_patient_bundle(patient_id: str, fhir_base_url: str | None = None) -> dict[str, Any]:
    """Fetch complete patient data bundle from HAPI FHIR server using $everything operation.

    Args:
        patient_id: FHIR Patient resource ID
        fhir_base_url: Optional override for FHIR server URL

    Returns:
        FHIR Bundle containing all patient resources

    Raises:
        requests.RequestException: If FHIR server is unreachable
        ValueError: If patient not found or invalid response
    """
    base_url = fhir_base_url or HAPI_FHIR_URL
    # Use FHIR $everything operation to get complete patient record
    url = f"{base_url}/Patient/{patient_id}/$everything"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        bundle = response.json()

        # Validate it's a FHIR Bundle
        if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
            raise ValueError(f"Invalid FHIR response: expected Bundle, got {type(bundle)}")

        return bundle

    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch patient {patient_id} from FHIR server: {e}") from e
