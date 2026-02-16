#!/usr/bin/env python3
"""Transform Justine Schoen's FHIR bundle:
1. Remove breast cancer entries after April 2025
2. Shift all dates forward by 6 months
3. Remove entries after Jan 16, 2026
"""

import json
import re
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

INPUT_FILE = "/home/claw/src/MedAudit/ehr/mod_Justine412_Garnett735_Schoen8_39b7de4b-abf2-d772-461e-193e503a035b.json"

BREAST_CANCER_KEYWORDS = [
    "malignant neoplasm of breast",
    "screening for malignant neoplasm of breast",
    "screening mammography",
    "mammography (procedure)",
    "ultrasonography of bilateral breasts",
    "biopsy of breast",
    "lumpectomy of breast",
    "screening surveillance",
    "chemotherapy",
    "doxorubicin",
    "tamoxifen",
    "her2",
    "erbb2",
    "estrogen receptor",
    "progesterone receptor",
    "cancer treatment",
    "tumor",
]

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})(T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2})$"
)

CUTOFF_STEP1 = date(2025, 4, 30)
CUTOFF_STEP3 = date(2026, 1, 16)


def extract_dates(entry):
    """Extract all date strings from a serialized entry and return as date objects."""
    text = json.dumps(entry)
    matches = DATE_RE.findall(text)
    dates = []
    for m in matches:
        try:
            dates.append(date.fromisoformat(m))
        except ValueError:
            pass
    return dates


def is_breast_cancer_entry(entry):
    """Check if an entry contains breast cancer keywords."""
    text = json.dumps(entry).lower()
    return any(kw in text for kw in BREAST_CANCER_KEYWORDS)


def shift_date_string(s):
    """Shift a FHIR date or datetime string forward by 6 months."""
    # Try datetime first
    m = DATETIME_RE.match(s)
    if m:
        date_part = m.group(1)
        rest = m.group(2)
        d = date.fromisoformat(date_part)
        d_shifted = d + relativedelta(months=6)
        return d_shifted.isoformat() + rest

    # Try date-only
    if DATE_ONLY_RE.match(s):
        d = date.fromisoformat(s)
        d_shifted = d + relativedelta(months=6)
        return d_shifted.isoformat()

    return s


def shift_dates_in_obj(obj):
    """Recursively walk JSON and shift all date/datetime strings."""
    if isinstance(obj, dict):
        return {k: shift_dates_in_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [shift_dates_in_obj(item) for item in obj]
    elif isinstance(obj, str):
        return shift_date_string(obj)
    else:
        return obj


def main():
    with open(INPUT_FILE) as f:
        bundle = json.load(f)

    original_count = len(bundle["entry"])
    print(f"Original entry count: {original_count}")

    # Step 1: Remove breast cancer entries after April 2025
    kept = []
    removed_step1 = 0
    for entry in bundle["entry"]:
        dates = extract_dates(entry)
        if is_breast_cancer_entry(entry) and dates:
            earliest = min(dates)
            if earliest > CUTOFF_STEP1:
                removed_step1 += 1
                continue
        kept.append(entry)
    bundle["entry"] = kept
    print(f"Step 1: Removed {removed_step1} breast cancer entries after {CUTOFF_STEP1}")
    print(f"  Remaining: {len(bundle['entry'])}")

    # Step 2: Shift all dates forward by 6 months
    bundle = shift_dates_in_obj(bundle)
    print("Step 2: Shifted all dates forward by 6 months")

    # Step 3: Remove entries after Jan 16, 2026
    kept = []
    removed_step3 = 0
    for entry in bundle["entry"]:
        dates = extract_dates(entry)
        if dates:
            earliest = min(dates)
            if earliest > CUTOFF_STEP3:
                removed_step3 += 1
                continue
        kept.append(entry)
    bundle["entry"] = kept
    print(f"Step 3: Removed {removed_step3} entries after {CUTOFF_STEP3}")
    print(f"  Final count: {len(bundle['entry'])}")

    # Write output
    with open(INPUT_FILE, "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"\nWrote transformed bundle to {INPUT_FILE}")

    # Verification
    print("\n--- Verification ---")
    with open(INPUT_FILE) as f:
        result = json.load(f)
    print(f"Valid JSON: Yes")
    print(
        f"Entry count: {len(result['entry'])} (removed {original_count - len(result['entry'])})"
    )

    # Check birthDate
    patient = result["entry"][0]["resource"]
    print(f"birthDate: {patient['birthDate']} (expected 1979-02-12)")

    # Check no dates after cutoff
    all_dates = extract_dates(result)
    late_dates = [d for d in all_dates if d > CUTOFF_STEP3]
    print(f"Dates after {CUTOFF_STEP3}: {len(late_dates)}")
    if late_dates:
        print(f"  WARNING: Found late dates: {sorted(set(late_dates))[:10]}")

    # Check cancer diagnosis shift
    for entry in result["entry"]:
        text = json.dumps(entry).lower()
        if "malignant neoplasm of breast" in text:
            dates = extract_dates(entry)
            if dates:
                print(f"Cancer diagnosis entry dates: {sorted(dates)}")
            break


if __name__ == "__main__":
    main()
