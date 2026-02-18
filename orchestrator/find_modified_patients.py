#!/usr/bin/env python3
"""
Find patients with FHIR records modified after a given timestamp.

Queries a FHIR server for all clinical resource types that have been
added or updated after the specified ISO datetime, then extracts the
associated patient IDs.

Usage:
    python find_modified_patients.py <iso-datetime> [--fhir-url URL]

Examples:
    python find_modified_patients.py 2025-01-01T00:00:00Z
    python find_modified_patients.py 2025-06-15T12:30:00-05:00 --fhir-url http://fhir.example.com/fhir
    python find_modified_patients.py 2025-01-01
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

import requests

# Default FHIR server URL (matches local HAPI FHIR docker setup)
DEFAULT_FHIR_URL = "http://localhost:9080/fhir"

# Resource types to scan, grouped by how they reference a patient.
# Key = search parameter name that points to the patient.
# Most clinical resources use "patient" or "subject".
RESOURCE_PATIENT_PARAM = {
    # Core clinical
    "Encounter": "patient",
    "Condition": "patient",
    "Observation": "patient",
    "DiagnosticReport": "patient",
    "ServiceRequest": "patient",
    "Procedure": "patient",
    "MedicationRequest": "patient",
    "MedicationAdministration": "patient",
    "MedicationStatement": "patient",
    "AllergyIntolerance": "patient",
    "Immunization": "patient",
    "CarePlan": "patient",
    "ClinicalImpression": "patient",
    "DocumentReference": "patient",
    "ImagingStudy": "patient",
    "EpisodeOfCare": "patient",
    "Flag": "patient",
    "Goal": "patient",
    "Communication": "patient",
    "Task": "patient",
    "Appointment": "actor",
    "Consent": "patient",
    "FamilyMemberHistory": "patient",
    "Claim": "patient",
}


def extract_patient_id(resource: dict) -> Optional[str]:
    """Extract patient ID from a FHIR resource's subject/patient reference."""
    # Try "subject" first (most clinical resources), then "patient"
    for ref_field in ("subject", "patient"):
        ref_obj = resource.get(ref_field)
        if ref_obj and isinstance(ref_obj, dict):
            reference = ref_obj.get("reference", "")
            if reference.startswith("Patient/"):
                return reference.split("Patient/")[1].split("/")[0]

    # For Appointment, check participant list for patient actors
    if resource.get("resourceType") == "Appointment":
        for participant in resource.get("participant", []):
            actor = participant.get("actor", {})
            reference = actor.get("reference", "")
            if reference.startswith("Patient/"):
                return reference.split("Patient/")[1].split("/")[0]

    return None


def scan_modified_resources(
    fhir_url: str,
    resource_type: str,
    since: str,
    session: requests.Session,
    patient_latest: dict[str, str],
) -> list[dict]:
    """Fetch all resources of a given type modified after `since`."""
    resources = []
    url = f"{fhir_url}/{resource_type}"
    params = {
        "_lastUpdated": f"gt{since}",
        "_sort": "-_lastUpdated",
        "_count": "100",
    }

    while url:
        try:
            resp = session.get(url, params=params)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Warning: Failed to query {resource_type}: {e}", file=sys.stderr)
            break

        bundle = resp.json()

        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if not resource:
                continue
            if resource_type == "Patient":
                pid = resource.get("id")
            else:
                pid = extract_patient_id(resource)
            if not pid:
                continue
            last_updated = resource.get("meta", {}).get("lastUpdated", "")
            if last_updated > patient_latest.get(pid, ""):
                patient_latest[pid] = last_updated

        # Follow pagination
        url = None
        params = None  # params are embedded in the "next" link
        for link in bundle.get("link", []):
            if link.get("relation") == "next":
                url = link.get("url")
                break


def find_modified_patients(fhir_url: str, since: str, patient_latest: dict[str, str]) -> None:
    """Find all patients with records modified after `since`.

    Populates patient_latest, mapping patient ID to the most recent
    _lastUpdated timestamp. Raises ConnectionError if the FHIR server
    is unreachable.
    """
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/fhir+json",
        }
    )

    # Test connection
    try:
        resp = session.get(f"{fhir_url}/metadata", timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"Cannot connect to FHIR server at {fhir_url}: {e}") from e

    # Check for new/modified Patient resources directly
    scan_modified_resources(fhir_url, "Patient", since, session, patient_latest)

    # Scan each clinical resource type
    for resource_type in RESOURCE_PATIENT_PARAM:
        scan_modified_resources(fhir_url, resource_type, since, session, patient_latest)


def _args_parse_iso_datetime(dt_string: str) -> str:
    """Validate and normalize an ISO datetime string for FHIR queries."""
    # Accept date-only (e.g. 2025-01-01) or full datetime
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            datetime.strptime(dt_string.replace("Z", "+0000"), fmt)
            return dt_string
        except ValueError:
            continue
    raise ValueError(
        f"Invalid ISO datetime: '{dt_string}'. "
        "Expected format like 2025-01-01T00:00:00Z or 2025-01-01"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Find patients with FHIR records modified after a given timestamp."
    )
    parser.add_argument(
        "since",
        help="ISO datetime string (e.g. 2025-01-01T00:00:00Z or 2025-01-01)",
    )
    parser.add_argument(
        "--fhir-url",
        default=DEFAULT_FHIR_URL,
        help=f"FHIR server base URL (default: {DEFAULT_FHIR_URL})",
    )

    args = parser.parse_args()

    # Validate the datetime
    try:
        since = _args_parse_iso_datetime(args.since)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    patient_latest: dict[str, str] = {}
    try:
        find_modified_patients(args.fhir_url, since, patient_latest)
    except ConnectionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not patient_latest:
        print(f"No patients found with records modified after {since}")
        return

    # Sort by most recently updated first
    sorted_patients = sorted(patient_latest.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{len(sorted_patients)} patient(s) with records modified after {since}:\n")
    print(f"  {'Patient ID':<40} {'Last Updated'}")
    print(f"  {'-' * 40} {'-' * 25}")
    for pid, last_updated in sorted_patients:
        print(f"  {pid:<40} {last_updated}")


if __name__ == "__main__":
    main()
