#!/usr/bin/env python3
"""Transform Richelle Wiegand's FHIR bundle:
1. Remove all entries from urn:uuid:943fec3e-ac5a-2284-cbeb-2414bd552323 onward,
   except keep screening mammography and ultrasound procedure records (entries 48-49)
2. Shift all dates forward by 8 months and 7 days (May 23 2025 -> Jan 30 2026)
3. Remove any entries with earliest date after Jan 30 2026
"""

import json
import re
from datetime import date
from dateutil.relativedelta import relativedelta

INPUT_FILE = "/home/claw/src/MedAudit/ehr/mod_Richelle340_Wiegand701_943fec3e-ac5a-2284-2b4f-ce652b6f09d3.json"

TARGET_UUID = "urn:uuid:943fec3e-ac5a-2284-cbeb-2414bd552323"
SHIFT = relativedelta(months=8, days=7)
CUTOFF = date(2026, 1, 30)

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2})$")

# UUIDs of the imaging procedure records to preserve
IMAGING_UUIDS = {
    "urn:uuid:943fec3e-ac5a-2284-7b9d-a05b68c7e097",  # screening mammography (entry 48)
    "urn:uuid:943fec3e-ac5a-2284-d6f8-acad375cff74",  # ultrasonography (entry 49)
}


def extract_dates(entry):
    text = json.dumps(entry)
    dates = []
    for m in DATE_RE.findall(text):
        try:
            dates.append(date.fromisoformat(m))
        except ValueError:
            pass
    return dates


def shift_date_string(s):
    m = DATETIME_RE.match(s)
    if m:
        d = date.fromisoformat(m.group(1))
        return (d + SHIFT).isoformat() + m.group(2)
    if DATE_ONLY_RE.match(s):
        d = date.fromisoformat(s)
        return (d + SHIFT).isoformat()
    return s


def shift_dates_in_obj(obj):
    if isinstance(obj, dict):
        return {k: shift_dates_in_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [shift_dates_in_obj(item) for item in obj]
    elif isinstance(obj, str):
        return shift_date_string(obj)
    return obj


def main():
    with open(INPUT_FILE) as f:
        bundle = json.load(f)

    original_count = len(bundle["entry"])
    print(f"Original entry count: {original_count}")

    # Step 1: Find cut point and remove entries, preserving imaging procedures
    cut_index = None
    imaging_entries = []
    for i, entry in enumerate(bundle["entry"]):
        if entry.get("fullUrl") == TARGET_UUID:
            cut_index = i
            break

    if cut_index is None:
        print("ERROR: Target UUID not found!")
        return

    print(f"Cut point: entry {cut_index} ({TARGET_UUID})")

    # Extract imaging procedures from after the cut point before removing
    for entry in bundle["entry"][cut_index:]:
        if entry.get("fullUrl") in IMAGING_UUIDS:
            imaging_entries.append(entry)
            print(f"  Preserving imaging: {entry['fullUrl'][-12:]} | {entry['resource']['code']['coding'][0]['display']}")

    # Keep entries before cut point + imaging procedures
    kept = bundle["entry"][:cut_index] + imaging_entries
    removed_step1 = original_count - len(kept)
    bundle["entry"] = kept
    print(f"Step 1: Removed {removed_step1} entries (kept {len(kept)})")

    # Step 2: Shift all dates
    bundle = shift_dates_in_obj(bundle)
    print(f"Step 2: Shifted all dates by 8 months 7 days")

    # Step 3: Remove entries after cutoff
    kept = []
    removed_step3 = 0
    for entry in bundle["entry"]:
        dates = extract_dates(entry)
        if dates:
            earliest = min(dates)
            if earliest > CUTOFF:
                removed_step3 += 1
                continue
        kept.append(entry)
    bundle["entry"] = kept
    print(f"Step 3: Removed {removed_step3} entries after {CUTOFF}")
    print(f"  Final count: {len(bundle['entry'])}")

    # Write output
    with open(INPUT_FILE, "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"\nWrote to {INPUT_FILE}")

    # Verification
    print("\n--- Verification ---")
    with open(INPUT_FILE) as f:
        result = json.load(f)
    print(f"Valid JSON: Yes")
    print(f"Entry count: {len(result['entry'])} (removed {original_count - len(result['entry'])})")

    patient = result["entry"][0]["resource"]
    print(f"birthDate: {patient['birthDate']}")

    # Verify May 23 shifted correctly
    all_dates = extract_dates(result)
    if date(2026, 1, 30) in all_dates:
        print(f"May 23 2025 shifted to Jan 30 2026: Yes")
    late = [d for d in all_dates if d > CUTOFF]
    print(f"Dates after {CUTOFF}: {len(late)}")
    if late:
        print(f"  Late dates: {sorted(set(late))[:10]}")

    # Show final entries
    print("\nFinal entries:")
    for i, entry in enumerate(result["entry"]):
        res = entry.get("resource", {})
        rtype = res.get("resourceType", "?")
        code = ""
        if "code" in res:
            codings = res["code"].get("coding", [])
            if codings:
                code = codings[0].get("display", "")
        if not code and "type" in res and isinstance(res["type"], list):
            for t in res["type"]:
                codings = t.get("coding", [])
                if codings:
                    code = codings[0].get("display", "")
                    break
        dates = extract_dates(entry)
        earliest = min(dates) if dates else "?"
        print(f"  [{i}] {str(earliest):12s} | {rtype:25s} | {code}")


if __name__ == "__main__":
    main()
