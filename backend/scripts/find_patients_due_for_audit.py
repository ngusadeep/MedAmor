#!/usr/bin/env python3
"""
Find patients needing audit based on two signals:

  1. Next audit due   — patients whose next_audit_date >= --lastrun (from DB)
  2. EHR modified     — patients with FHIR records modified since --lastrun

Usage (inside the container):
    python scripts/find_patients_due_for_audit.py --lastrun 2025-01-01T00:00:00Z
    python scripts/find_patients_due_for_audit.py --lastrun 2025-01-01 --fhir-url http://fhir.example.com/fhir

    # Print patient IDs only (default):
    python scripts/find_patients_due_for_audit.py --lastrun 2025-01-01T00:00:00Z

    # Find and immediately trigger audits via the API:
    python scripts/find_patients_due_for_audit.py --lastrun 2025-01-01T00:00:00Z --trigger --password chief123

Via docker exec (while the stack is running):
    docker exec medaudit_backend python scripts/find_patients_due_for_audit.py --lastrun 2025-01-01T00:00:00Z

Via docker run (one-shot, against the same network):
    docker run --rm --env-file .env --network medaudit_default medaudit-app \
        python scripts/find_patients_due_for_audit.py --lastrun 2025-01-01T00:00:00Z
"""

import argparse
import sys
from datetime import datetime, timezone
from typing import Optional

import requests
from sqlalchemy import func

from app.core.database import SessionLocal
from app.models.audit_report import AuditReport


# ---------------------------------------------------------------------------
# FHIR configuration
# ---------------------------------------------------------------------------

DEFAULT_FHIR_URL = "http://localhost:8001/fhir"

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


# ---------------------------------------------------------------------------
# FHIR helpers
# ---------------------------------------------------------------------------

def extract_patient_id(resource: dict) -> Optional[str]:
    """Extract patient ID from a FHIR resource's subject/patient reference."""
    for ref_field in ("subject", "patient"):
        ref_obj = resource.get(ref_field)
        if ref_obj and isinstance(ref_obj, dict):
            reference = ref_obj.get("reference", "")
            if reference.startswith("Patient/"):
                return reference.split("Patient/")[1].split("/")[0]

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
) -> None:
    """Fetch all resources of a given type modified after `since`."""
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


def find_modified_patients(
    fhir_url: str, since: str, patient_latest: dict[str, str]
) -> None:
    """Populate patient_latest with patients whose FHIR records changed after `since`.

    Raises ConnectionError if the FHIR server is unreachable.
    """
    session = requests.Session()
    session.headers.update({"Accept": "application/fhir+json"})

    try:
        resp = session.get(f"{fhir_url}/metadata", timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"Cannot connect to FHIR server at {fhir_url}: {e}") from e

    scan_modified_resources(fhir_url, "Patient", since, session, patient_latest)
    for resource_type in RESOURCE_PATIENT_PARAM:
        scan_modified_resources(fhir_url, resource_type, since, session, patient_latest)


# ---------------------------------------------------------------------------
# Database query
# ---------------------------------------------------------------------------

def parse_iso_datetime(dt_string: str) -> datetime:
    """Parse an ISO datetime string into a timezone-aware datetime."""
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(dt_string.replace("Z", "+0000"), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    raise ValueError(
        f"Invalid ISO datetime: '{dt_string}'. "
        "Expected format like 2025-01-01T00:00:00Z or 2025-01-01"
    )


def find_patients_due_for_audit(lastrun: datetime) -> list[tuple[str, datetime]]:
    """Query audit_reports for patients with next_audit_date >= lastrun.

    These are patients that the AI Agent has previously said would be due for
    review on a next_audit_date.

    Groups by patient_id and returns the earliest next_audit_date per patient.
    Returns a list of (patient_id, next_audit_date) sorted by next_audit_date.
    """
    db = SessionLocal()
    try:
        rows = (
            db.query(
                AuditReport.patient_id,
                func.min(AuditReport.next_audit_date).label("next_audit_date"),
            )
            .filter(AuditReport.next_audit_date >= lastrun)
            .group_by(AuditReport.patient_id)
            .order_by(func.min(AuditReport.next_audit_date))
            .all()
        )
        return [(patient_id, next_audit_date) for patient_id, next_audit_date in rows]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Audit trigger
# ---------------------------------------------------------------------------

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_USERNAME = "chief@medarmor.com"


def trigger_audits(api_url: str, username: str, password: str, patient_ids: list[str]) -> None:
    """Login to the API and POST /api/jobs/batch for all patient_ids."""
    api_url = api_url.rstrip("/")

    # Authenticate
    try:
        resp = requests.post(
            f"{api_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error: Failed to authenticate: {e}", file=sys.stderr)
        sys.exit(1)

    token = resp.json().get("access_token")
    if not token:
        print("  Error: No access_token in login response", file=sys.stderr)
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Submit batch job
    try:
        resp = requests.post(
            f"{api_url}/api/jobs/batch",
            json={"patient_ids": patient_ids, "triggered_by": "find_patients_due_for_audit"},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error: Failed to submit batch job: {e}", file=sys.stderr)
        sys.exit(1)

    jobs = resp.json()
    print(f"\n  Queued {len(jobs)} audit job(s):\n")
    print(f"  {'Job ID':<38} {'Patient ID':<55} {'Status'}")
    print(f"  {'-' * 38} {'-' * 55} {'-' * 10}")
    for job in jobs:
        print(f"  {job['id']:<38} {job['patient_id']:<55} {job['status']}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Find patients needing audit: next audit due (DB) "
            "and/or EHR records modified (FHIR) since --lastrun."
        )
    )
    parser.add_argument(
        "--lastrun",
        required=True,
        metavar="DATETIME",
        help="ISO datetime of the last run (e.g. 2025-01-01T00:00:00Z or 2025-01-01)",
    )
    parser.add_argument(
        "--fhir-url",
        default=DEFAULT_FHIR_URL,
        help=f"FHIR server base URL (default: {DEFAULT_FHIR_URL})",
    )
    parser.add_argument(
        "--trigger",
        action="store_true",
        help="Submit found patients to POST /api/jobs/batch to trigger audits",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Backend API base URL used when --trigger is set (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--username",
        default=DEFAULT_USERNAME,
        help=f"API username for authentication (default: {DEFAULT_USERNAME})",
    )
    parser.add_argument(
        "--password",
        help="API password for authentication (required when --trigger is set)",
    )
    args = parser.parse_args()

    if args.trigger and not args.password:
        parser.error("--password is required when --trigger is set")

    try:
        lastrun = parse_iso_datetime(args.lastrun)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    since_str = args.lastrun  # raw string passed to FHIR _lastUpdated filter

    # --- DB: patients with next audit due ---
    print(f"Since   : {lastrun.isoformat()}")
    print("\n[1/2] Querying database for patients with next audit due ...")
    try:
        due_rows = find_patients_due_for_audit(lastrun)
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)

    if due_rows:
        print(f"\n  {len(due_rows)} patient(s) with next audit due:\n")
        print(f"  {'Patient ID':<55} {'Next Audit Date'}")
        print(f"  {'-' * 55} {'-' * 30}")
        for patient_id, next_audit_date in due_rows:
            date_str = next_audit_date.isoformat() if next_audit_date else "N/A"
            print(f"  {patient_id:<55} {date_str}")
    else:
        print(f"  No patients found with next_audit_date >= {lastrun.isoformat()}")

    # --- FHIR: patients with modified EHR records ---
    print(f"\n[2/2] Querying FHIR server for patients with modified EHR records ...")
    patient_latest: dict[str, str] = {}
    try:
        find_modified_patients(args.fhir_url, since_str, patient_latest)
    except ConnectionError as e:
        print(f"  Warning: {e}", file=sys.stderr)
        print("  Skipping EHR check.")
        patient_latest = {}

    if patient_latest:
        sorted_ehr = sorted(patient_latest.items(), key=lambda x: x[1], reverse=True)
        print(f"\n  {len(sorted_ehr)} patient(s) with modified EHR records:\n")
        print(f"  {'Patient ID':<40} {'EHR Last Updated'}")
        print(f"  {'-' * 40} {'-' * 25}")
        for pid, last_updated in sorted_ehr:
            print(f"  {pid:<40} {last_updated}")
    else:
        print(f"  No patients found with EHR records modified since {since_str}")

    # --- Trigger audits if requested ---
    if args.trigger:
        all_patient_ids = list(
            {pid for pid, _ in due_rows} | set(patient_latest.keys())
        )
        if not all_patient_ids:
            print("\nNo patients found — nothing to trigger.")
            return
        print(f"\n[Trigger] Submitting {len(all_patient_ids)} patient(s) to {args.api_url} ...")
        trigger_audits(args.api_url, args.username, args.password, all_patient_ids)


if __name__ == "__main__":
    main()
