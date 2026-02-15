#!/usr/bin/env python3
"""Migration script to populate PostgreSQL database with patient data from files."""

import os
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import SessionLocal, create_tables
from app.database.patient_service import create_patient


def extract_patient_name_from_text(ehr_text: str) -> str | None:
    """Extract patient name from EHR text if possible."""
    lines = ehr_text.split('\n')
    for line in lines:
        if line.startswith('Patient: ') or line.startswith('# EHR Timeline'):
            continue
        if 'Patient ID:' in line:
            continue
        # Try to extract name from the first meaningful line
        if line.strip() and not line.startswith('['):
            # Look for name patterns like "John Doe (id: ...)"
            if '(id:' in line:
                name = line.split('(id:')[0].strip()
                return name if name else None
    return None


def migrate_patients_from_files():
    """Migrate patient data from files to database."""
    print("Starting patient data migration...")

    # Create tables if they don't exist
    create_tables()
    print("Database tables created/verified.")

    # Path to patients directory
    patients_dir = Path(__file__).resolve().parent / "patients"
    if not patients_dir.is_dir():
        print(f"Patients directory not found: {patients_dir}")
        return

    migrated_count = 0

    with SessionLocal() as db:
        # Clear existing data (optional, for re-migration)
        db.execute("DELETE FROM patients")
        db.commit()

        # Process each patient directory
        for patient_path in sorted(patients_dir.iterdir()):
            if not patient_path.is_dir():
                continue

            patient_id = patient_path.name

            # Find the full.txt file
            full_txt = patient_path / "full.txt"
            if not full_txt.is_file():
                print(f"Skipping {patient_id}: full.txt not found")
                continue

            try:
                ehr_text = full_txt.read_text(encoding="utf-8", errors="replace")
                patient_name = extract_patient_name_from_text(ehr_text)

                # Create patient record
                create_patient(
                    db=db,
                    patient_id=patient_id,
                    patient_name=patient_name,
                    ehr_text=ehr_text
                )

                migrated_count += 1
                print(f"Migrated patient {patient_id}: {patient_name or 'Unknown name'}")

            except Exception as e:
                print(f"Error migrating patient {patient_id}: {e}")
                continue

    print(f"Migration completed! Migrated {migrated_count} patients.")


if __name__ == "__main__":
    migrate_patients_from_files()