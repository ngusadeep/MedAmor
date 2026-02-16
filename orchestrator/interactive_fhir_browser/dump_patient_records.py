#!/usr/bin/env python3
"""Dump full text timeline records for all patients from the FHIR server."""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

# Add parent directory to path for importing fhir_reader
sys.path.insert(0, str(Path(__file__).parent.parent))

from fhir_reader.timeline import FHIRTimelineConverter

FHIR_SERVER_URL = "http://localhost:9080/fhir"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patient_records")


def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r"[^\w\s-]", "", name)
    sanitized = re.sub(r"\s+", "_", sanitized)
    return sanitized.lower()


def format_patient_name(patient: dict) -> str:
    if "name" not in patient or len(patient["name"]) == 0:
        return "Unknown"
    name = patient["name"][0]
    parts = []
    if "given" in name:
        parts.extend(name["given"])
    if "family" in name:
        parts.append(name["family"])
    return " ".join(parts) if parts else "Unknown"


def main():
    session = requests.Session()
    session.headers.update({"Accept": "application/fhir+json"})

    # Test connection
    try:
        resp = session.get(f"{FHIR_SERVER_URL}/metadata", timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"Cannot connect to FHIR server at {FHIR_SERVER_URL}: {e}")
        return 1

    # Fetch all patients
    patients = []
    url = f"{FHIR_SERVER_URL}/Patient?_count=100"
    while url:
        resp = session.get(url)
        resp.raise_for_status()
        bundle = resp.json()
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                patients.append(resource)
        # Follow next link for pagination
        url = None
        for link in bundle.get("link", []):
            if link.get("relation") == "next":
                url = link["url"]
                break

    if not patients:
        print("No patients found.")
        return 1

    print(f"Found {len(patients)} patients.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for patient in patients:
        patient_id = patient.get("id", "unknown")
        patient_name = format_patient_name(patient)
        safe_name = sanitize_filename(patient_name)

        print(f"  {patient_name} (ID: {patient_id}) ...", end=" ", flush=True)

        # Fetch $everything
        resp = session.get(
            f"{FHIR_SERVER_URL}/Patient/{patient_id}/$everything",
            params={"_count": 1000},
        )
        resp.raise_for_status()
        everything_bundle = resp.json()

        # Convert to timeline
        converter = FHIRTimelineConverter(everything_bundle)
        timeline = converter.convert(include_costs=True, include_codes=False)

        # Write file
        filename = f"{patient_id}_{safe_name}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w") as f:
            f.write(timeline)

        print(f"-> {filename}")

    print(f"\nDone. Files written to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
