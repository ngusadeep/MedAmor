#!/usr/bin/env python3
"""Migrate patient data from ehr/fhir/*.json FHIR R4 bundles into the EHR database.

Run once before starting the server (or at Docker startup when DB is empty):
    python ehr/migrate_from_fhir.py

The script:
  1. Drops and recreates the patients table (handles schema changes cleanly).
  2. For every *.json in ehr/fhir/, extracts patient demographics from the
     FHIR Patient resource and inserts a row — without pre-generating the
     timeline text (that happens lazily on first audit request).
"""

import json
import sys
from pathlib import Path

from sqlalchemy import text

# Ensure /app is in sys.path so `ehr.*` imports resolve when run from /app
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from ehr.app.database.connection import Base, SessionLocal, engine
from ehr.app.database.models import Patient  # noqa: F401 — ensures model is registered
from ehr.app.database.patient_service import create_patient


FHIR_DIR = Path(__file__).resolve().parent / "fhir"


def _extract_demographics(bundle: dict) -> dict:
    """Pull name + demographics from the Patient resource inside a bundle."""
    info: dict = {
        "patient_id": None,
        "patient_name": None,
        "birth_date": None,
        "gender": None,
        "address": None,
        "phone": None,
        "race": None,
        "ethnicity": None,
        "marital_status": None,
    }
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") != "Patient":
            continue

        info["patient_id"] = resource.get("id")

        # Name
        names = resource.get("name", [])
        if names:
            n = names[0]
            parts = n.get("prefix", []) + n.get("given", []) + [n.get("family", "")]
            info["patient_name"] = " ".join(p for p in parts if p).strip() or None

        info["birth_date"] = resource.get("birthDate")
        info["gender"] = resource.get("gender")

        # Address
        addrs = resource.get("address", [])
        if addrs:
            a = addrs[0]
            info["address"] = ", ".join(filter(None, [
                ", ".join(a.get("line", [])),
                a.get("city"), a.get("state"), a.get("postalCode"),
            ])) or None

        # Phone
        for t in resource.get("telecom", []):
            if t.get("system") == "phone":
                info["phone"] = t.get("value")
                break

        # Marital status
        ms = resource.get("maritalStatus", {})
        info["marital_status"] = ms.get("text") or (
            (ms.get("coding") or [{}])[0].get("display")
        )

        # Race / ethnicity (US Core extensions)
        for ext in resource.get("extension", []):
            url = ext.get("url", "").lower()
            for sub in ext.get("extension", []):
                if sub.get("url") == "text":
                    if "race" in url:
                        info["race"] = sub.get("valueString")
                    elif "ethnicity" in url:
                        info["ethnicity"] = sub.get("valueString")
        break  # only one Patient resource per bundle

    return info


def migrate() -> None:
    if not FHIR_DIR.is_dir():
        print(f"ERROR: FHIR directory not found: {FHIR_DIR}")
        sys.exit(1)

    fhir_files = sorted(FHIR_DIR.glob("*.json"))
    if not fhir_files:
        print(f"No *.json files found in {FHIR_DIR}")
        sys.exit(1)

    print(f"Found {len(fhir_files)} FHIR bundles in {FHIR_DIR}")

    # Drop + recreate to handle schema changes
    print("Recreating patients table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS patients CASCADE"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    print("Table ready.")

    ok = skipped = errors = 0

    with SessionLocal() as db:
        for fhir_file in fhir_files:
            try:
                raw = fhir_file.read_text(encoding="utf-8", errors="replace")
                bundle = json.loads(raw)
            except Exception as e:
                print(f"  SKIP {fhir_file.name}: JSON parse error — {e}")
                errors += 1
                continue

            demo = _extract_demographics(bundle)
            patient_id = demo["patient_id"]

            if not patient_id:
                print(f"  SKIP {fhir_file.name}: no Patient.id found")
                skipped += 1
                continue

            try:
                create_patient(
                    db,
                    patient_id=patient_id,
                    patient_name=demo["patient_name"],
                    birth_date=demo["birth_date"],
                    gender=demo["gender"],
                    address=demo["address"],
                    phone=demo["phone"],
                    race=demo["race"],
                    ethnicity=demo["ethnicity"],
                    marital_status=demo["marital_status"],
                    fhir_json=raw,
                )
                ok += 1
                print(f"  OK  {patient_id}  {demo['patient_name'] or '(no name)'}")
            except Exception as e:
                print(f"  ERR {patient_id}: {e}")
                errors += 1

    print(f"\nDone. {ok} imported, {skipped} skipped, {errors} errors.")


if __name__ == "__main__":
    migrate()
