#!/usr/bin/env python3
"""Convert FHIR bundles in fhir/ to text timelines in patients/<id>/full.txt.

Run from ehr dir. Backend uses patients/ when EHR_DATA_ROOT points to ehr.
Skips *Information*.json. Patient id = first Patient resource id in bundle.
"""

import json
import re
import sys
from pathlib import Path


def _date_from_resource(res: dict) -> str | None:
    for key in ("onsetDateTime", "recordedDate", "effectiveDateTime", "period", "start", "performed"):
        v = res.get(key)
        if isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}", v):
            return v[:10]
        if isinstance(v, dict) and "start" in v:
            s = v["start"]
            if isinstance(s, str):
                return s[:10]
    return None


def _display(res: dict) -> str:
    if "code" in res and "text" in res.get("code", {}):
        return res["code"]["text"]
    if "code" in res and "coding" in res["code"]:
        codings = res["code"]["coding"]
        if codings and "display" in codings[0]:
            return codings[0]["display"]
    if "name" in res and res["name"]:
        n = res["name"][0]
        given = n.get("given") or []
        family = n.get("family")
        if isinstance(family, str):
            family = [family]
        elif not family:
            family = []
        parts = list(given) + list(family)
        return " ".join(str(p) for p in parts if p)
    return res.get("id", "") or res.get("resourceType", "")


def bundle_to_timeline(bundle: dict) -> str:
    """Produce a simple timeline text from a FHIR bundle (no external deps)."""
    lines: list[tuple[str, str, str]] = []
    patient_id: str | None = None
    patient_name: str = ""

    for entry in bundle.get("entry") or []:
        res = entry.get("resource")
        if not res:
            continue
        rt = res.get("resourceType")
        if rt == "Patient" and patient_id is None:
            patient_id = res.get("id")
            patient_name = _display(res)
            lines.append(("", "Patient", f"{patient_name} (id: {patient_id})"))
            continue
        date = _date_from_resource(res)
        disp = _display(res)
        if rt in ("Condition", "Procedure", "Observation", "DiagnosticReport", "ImagingStudy", "Encounter", "ServiceRequest", "MedicationRequest"):
            lines.append((date or "", rt, disp))
    lines.sort(key=lambda x: (x[0] or "0000-00-00", x[1], x[2]))

    out = [f"# EHR Timeline\nPatient: {patient_name}\nPatient ID: {patient_id}\n"]
    for date, rtype, disp in lines:
        if date:
            out.append(f"\n[{date}] {rtype}: {disp}")
        else:
            out.append(f"\n{rtype}: {disp}")
    return "\n".join(out).strip() + "\n"


def main() -> None:
    ehr_root = Path(__file__).resolve().parent
    fhir_dir = ehr_root / "fhir"
    patients_dir = ehr_root / "patients"
    if not fhir_dir.is_dir():
        print("fhir/ not found; create it and put FHIR bundle JSONs there.", file=sys.stderr)
        sys.exit(1)
    patients_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted(fhir_dir.glob("*.json")):
        if "Information" in path.name:
            continue
        try:
            bundle = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Skip {path.name}: {e}", file=sys.stderr)
            continue
        patient_id = None
        for entry in bundle.get("entry") or []:
            res = entry.get("resource")
            if res and res.get("resourceType") == "Patient":
                patient_id = res.get("id")
                break
        if not patient_id:
            print(f"Skip {path.name}: no Patient resource", file=sys.stderr)
            continue
        timeline = bundle_to_timeline(bundle)
        out_dir = patients_dir / patient_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "full.txt").write_text(timeline, encoding="utf-8")
        count += 1
        print(f"  {path.name} -> patients/{patient_id}/full.txt")
    print(f"Done. {count} patients written to patients/.")


if __name__ == "__main__":
    main()
