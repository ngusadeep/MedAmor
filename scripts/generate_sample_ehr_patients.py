#!/usr/bin/env python3
"""Generate ~5 sample EHR patients from the template EHR-DATA_51674_* folder.

Run from repo root: python scripts/generate_sample_ehr_patients.py

Creates EHR-DATA_51675_* through EHR-DATA_51678_* so the mock EHR API lists 5 patients.
"""

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = REPO_ROOT / "EHR-DATA_51674_mrs_elinore878_barton704_"

# (patient_id, name_slug, display_name for Patient Name: line)
EXTRA_PATIENTS = [
    ("51675", "mr_john755_smith801", "Mr. John755 Smith801"),
    ("51676", "ms_maria662_jones912", "Ms. Maria662 Jones912"),
    ("51677", "dr_james883_wilson723", "Dr. James883 Wilson723"),
    ("51678", "mrs_sarah994_brown634", "Mrs. Sarah994 Brown634"),
]


def main() -> None:
    if not TEMPLATE_DIR.is_dir():
        print(f"Template not found: {TEMPLATE_DIR}")
        return
    txt_files = sorted(
        f for f in TEMPLATE_DIR.iterdir() if f.is_file() and f.suffix == ".txt"
    )
    if not txt_files:
        print("No .txt files in template dir")
        return

    # Template identifiers to replace
    old_id = "51674"
    old_slug = "mrs_elinore878_barton704"
    old_name = "Mrs. Elinore878 Barton704"
    # Elinore878 / Barton704 appear in content
    old_first = "Elinore878"
    old_last = "Barton704"

    for patient_id, name_slug, display_name in EXTRA_PATIENTS:
        new_dir = REPO_ROOT / f"EHR-DATA_{patient_id}_{name_slug}_"
        new_dir.mkdir(parents=True, exist_ok=True)

        for src in txt_files:
            content = src.read_text(encoding="utf-8", errors="replace")
            content = content.replace(
                f"Patient ID: {old_id}", f"Patient ID: {patient_id}"
            )
            content = content.replace(
                f"  Patient ID: {old_id}", f"  Patient ID: {patient_id}"
            )
            content = re.sub(rf"\b{re.escape(old_id)}\b", patient_id, content)
            content = content.replace(old_name, display_name)
            content = content.replace(f"  Name: {old_name}", f"  Name: {display_name}")

            # New filename: 51674_mrs_elinore878_barton704_full_... -> 51675_mr_john755_smith801_full_...
            base = src.name.replace(old_id, patient_id, 1).replace(
                old_slug, name_slug, 1
            )
            dest = new_dir / base
            dest.write_text(content, encoding="utf-8")
            print(f"  {dest.relative_to(REPO_ROOT)}")

        print(f"Created {new_dir.name}")

    print("Done. Mock EHR now has 5 patients (51674–51678).")


if __name__ == "__main__":
    main()
