#!/usr/bin/env python3
"""Copy patient_data flat files into ehr/patients/<patient_id>/full.txt for migration.

Reads from:
  - patient_data/patient_records2/*.txt
  - patient_data/*.txt (root-level .txt files only)

Uses the first segment of the filename (before the first _) as patient_id.
Example: 116197_richelle340_wiegand701.txt -> ehr/patients/116197/full.txt
"""

import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    patient_data = project_root / "patient_data"
    ehr_patients = project_root / "ehr" / "patients"

    if not patient_data.is_dir():
        print(f"patient_data not found: {patient_data}")
        return 1

    ehr_patients.mkdir(parents=True, exist_ok=True)

    # Collect all .txt files
    sources: list[Path] = []
    records2 = patient_data / "patient_records2"
    if records2.is_dir():
        sources.extend(sorted(records2.glob("*.txt")))
    for p in sorted(patient_data.glob("*.txt")):
        if p.is_file():
            sources.append(p)

    if not sources:
        print("No .txt files found in patient_data or patient_data/patient_records2")
        return 1

    copied = 0
    for src in sources:
        # patient_id = first segment of filename (e.g. 116197 from 116197_richelle340_wiegand701.txt)
        stem = src.stem
        patient_id = stem.split("_")[0] if "_" in stem else stem
        if not patient_id:
            continue

        dest_dir = ehr_patients / patient_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "full.txt"

        try:
            content = src.read_text(encoding="utf-8", errors="replace")
            dest_file.write_text(content, encoding="utf-8")
            copied += 1
        except OSError as e:
            print(f"Error copying {src.name}: {e}", file=sys.stderr)

    print(f"Copied {copied} patient files to {ehr_patients}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
