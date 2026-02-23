"""EHR patient data: discover and serve from disk or EHR service.

Supports two layouts (both under ehr_data_root):
- patients/<patient_id>/<export_type>.txt  (e.g. patients/abc123/full.txt) — preferred
- EHR-DATA_<id>_<name>_/ with .txt files — legacy
"""

import re
from pathlib import Path

from app.core.config import settings
from app.schemas.ehr import EHRPatientBundle, EHRPatientDetail, EHRPatientSummary


def _ehr_root() -> Path:
    return settings.ehr_data_root_resolved


def _discover_from_patients_dir(root: Path) -> list[tuple[str, str, list[str]]]:
    result: list[tuple[str, str, list[str]]] = []
    patients_dir = root / "patients"
    if not patients_dir.is_dir():
        return result
    for path in patients_dir.iterdir():
        if not path.is_dir():
            continue
        patient_id = path.name
        export_types = [f.stem for f in path.iterdir() if f.is_file() and f.suffix == ".txt"]
        if export_types:
            result.append((patient_id, patient_id, sorted(set(export_types))))
    return result


def _discover_from_ehr_data_folders(root: Path) -> list[tuple[str, str, list[str]]]:
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
        patient_id, name_slug = m.group(1), m.group(2)
        export_types = [
            file_pattern.match(f.name).group(1)
            for f in path.iterdir()
            if f.is_file() and f.suffix == ".txt" and file_pattern.match(f.name)
        ]
        if export_types:
            result.append((patient_id, name_slug, sorted(set(export_types))))
    return result


def _discover_patients() -> list[tuple[str, str, list[str]]]:
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


def get_patient_detail(patient_id: str) -> EHRPatientDetail | None:
    """Return patient demographics.  Falls back to minimal detail from disk if no EHR service."""
    if settings.ehr_service_url:
        from app.services.ehr_client import get_patient_detail_from_service
        return get_patient_detail_from_service(settings.ehr_service_url, patient_id)

    # Local disk: we only have the summary info; return what we can
    for pid, name_slug, etypes in _discover_patients():
        if pid == patient_id:
            return EHRPatientDetail(
                patient_id=pid,
                patient_name=name_slug.replace("_", " ").title() if name_slug != pid else None,
                timeline_ready=True,
            )
    return None


def get_patient_bundle(patient_id: str, export_type: str = "full") -> EHRPatientBundle | None:
    if settings.ehr_service_url:
        from app.services.ehr_client import get_patient_bundle_from_service
        return get_patient_bundle_from_service(settings.ehr_service_url, patient_id, export_type)

    root = _ehr_root()
    # 1) patients/<id>/<export_type>.txt
    txt = root / "patients" / patient_id / f"{export_type}.txt"
    if txt.is_file():
        return EHRPatientBundle(
            patient_id=patient_id,
            export_type=export_type,
            ehr_text=txt.read_text(encoding="utf-8", errors="replace"),
            image_refs=None,
        )
    # 2) Legacy EHR-DATA_* folder
    for path in root.iterdir():
        if not path.is_dir() or not path.name.startswith(f"EHR-DATA_{patient_id}_"):
            continue
        for f in path.iterdir():
            if f.is_file() and f.suffix == ".txt" and f"_{export_type}_" in f.name:
                return EHRPatientBundle(
                    patient_id=patient_id,
                    export_type=export_type,
                    ehr_text=f.read_text(encoding="utf-8", errors="replace"),
                    image_refs=None,
                )
        return None
    return None
