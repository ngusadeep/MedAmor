"""EHR patient data: discover and serve from disk.

Supports two layouts (both under ehr_data_root):
- patients/<patient_id>/<export_type>.txt  (e.g. patients/abc123/full.txt) — preferred
- EHR-DATA_<id>_<name>_/ with .txt files — legacy
"""

import re
from pathlib import Path

from app.core.config import settings
from app.schemas.ehr import EHRPatientBundle, EHRPatientSummary


def _ehr_root() -> Path:
    return settings.ehr_data_root_resolved


def _discover_from_patients_dir(root: Path) -> list[tuple[str, str, list[str]]]:
    """Discover (patient_id, name_slug, export_types) from root/patients/<id>/*.txt."""
    result: list[tuple[str, str, list[str]]] = []
    patients_dir = root / "patients"
    if not patients_dir.is_dir():
        return result
    for path in patients_dir.iterdir():
        if not path.is_dir():
            continue
        patient_id = path.name
        export_types: list[str] = []
        for f in path.iterdir():
            if f.is_file() and f.suffix == ".txt":
                export_types.append(f.stem)  # full.txt -> full
        if export_types:
            result.append((patient_id, patient_id, sorted(set(export_types))))
    return result


def _discover_from_ehr_data_folders(root: Path) -> list[tuple[str, str, list[str]]]:
    """Discover from legacy EHR-DATA_<id>_<name>_ folders."""
    result: list[tuple[str, str, list[str]]] = []
    pattern = re.compile(r"^EHR-DATA_(\d+)_(.+)_$")
    file_pattern = re.compile(
        r"^\d+_.+?_(full|handoff_complete|handoff_minimal|imaging_complete|imaging_minimal)_\d{8}_\d+\.txt$"
    )
    for path in root.iterdir():
        if not path.is_dir() or not path.name.startswith("EHR-DATA_"):
            continue
        m = pattern.match(path.name)
        if not m:
            continue
        patient_id = m.group(1)
        name_slug = m.group(2)
        export_types: list[str] = []
        for f in path.iterdir():
            if f.is_file() and f.suffix == ".txt" and file_pattern.match(f.name):
                export_types.append(file_pattern.match(f.name).group(1))
        if export_types:
            result.append((patient_id, name_slug, sorted(set(export_types))))
    return result


def _discover_patients() -> list[tuple[str, str, list[str]]]:
    """Merge discovery from patients/ and legacy EHR-DATA_* (no duplicates by patient_id)."""
    root = _ehr_root()
    if not root.exists():
        return []
    seen: set[str] = set()
    out: list[tuple[str, str, list[str]]] = []
    for patient_id, name_slug, export_types in _discover_from_patients_dir(root):
        if patient_id not in seen:
            seen.add(patient_id)
            out.append((patient_id, name_slug, export_types))
    for patient_id, name_slug, export_types in _discover_from_ehr_data_folders(root):
        if patient_id not in seen:
            seen.add(patient_id)
            out.append((patient_id, name_slug, export_types))
    return out


def list_patients() -> list[EHRPatientSummary]:
    """List patients: from EHR service if EHR_SERVICE_URL set, else from disk (patients/ or EHR-DATA_*)."""
    if settings.ehr_service_url:
        from app.services.ehr_client import list_patients_from_service

        return list_patients_from_service(settings.ehr_service_url)
    return [
        EHRPatientSummary(
            patient_id=pid,
            patient_name=(name.replace("_", " ").title() if name != pid else None),
            export_types=etypes,
        )
        for pid, name, etypes in _discover_patients()
    ]


def get_patient_bundle(
    patient_id: str, export_type: str = "full"
) -> EHRPatientBundle | None:
    """Load one patient: from EHR service if EHR_SERVICE_URL set, else from disk."""
    if settings.ehr_service_url:
        from app.services.ehr_client import get_patient_bundle_from_service

        return get_patient_bundle_from_service(
            settings.ehr_service_url, patient_id, export_type
        )
    root = _ehr_root()
    # 1) patients/<id>/<export_type>.txt
    patients_dir = root / "patients" / patient_id
    if patients_dir.is_dir():
        f = patients_dir / f"{export_type}.txt"
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="replace")
            return EHRPatientBundle(
                patient_id=patient_id,
                export_type=export_type,
                ehr_text=text,
                image_refs=None,
            )
    # 2) Legacy EHR-DATA_* folder
    for path in root.iterdir():
        if not path.is_dir() or not path.name.startswith("EHR-DATA_"):
            continue
        if not path.name.startswith(f"EHR-DATA_{patient_id}_"):
            continue
        for f in path.iterdir():
            if f.is_file() and f.suffix == ".txt" and f"_{export_type}_" in f.name:
                text = f.read_text(encoding="utf-8", errors="replace")
                return EHRPatientBundle(
                    patient_id=patient_id,
                    export_type=export_type,
                    ehr_text=text,
                    image_refs=None,
                )
        return None
    return None
