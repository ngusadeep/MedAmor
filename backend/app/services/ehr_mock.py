"""Mock EHR: discover and serve EHR-DATA_* .txt files from disk."""

import re
from pathlib import Path

from app.core.config import settings
from app.schemas.ehr import EHRPatientBundle, EHRPatientSummary


def _ehr_root() -> Path:
    return settings.ehr_data_root_resolved


def _discover_patients() -> list[tuple[str, str, list[str]]]:
    """Discover (patient_id, patient_name_slug, export_types) from EHR-DATA_* folders."""
    root = _ehr_root()
    if not root.exists():
        return []
    result: list[tuple[str, str, list[str]]] = []
    # Folder pattern: EHR-DATA_51674_mrs_elinore878_barton704_
    pattern = re.compile(r"^EHR-DATA_(\d+)_(.+)_$")
    for path in root.iterdir():
        if not path.is_dir():
            continue
        m = pattern.match(path.name)
        if not m:
            continue
        patient_id = m.group(1)
        name_slug = m.group(2)
        export_types: list[str] = []
        # Files: 51674_mrs_elinore878_barton704_full_20260201_113539.txt
        file_pattern = re.compile(r"^\d+_.+?_(full|handoff_complete|handoff_minimal|imaging_complete|imaging_minimal)_\d{8}_\d+\.txt$")
        for f in path.iterdir():
            if f.is_file() and f.suffix == ".txt":
                fm = file_pattern.match(f.name)
                if fm:
                    export_types.append(fm.group(1))
        if export_types:
            result.append((patient_id, name_slug, sorted(set(export_types))))
    return result


def list_patients() -> list[EHRPatientSummary]:
    """List patients available in mock EHR."""
    summaries = []
    for patient_id, name_slug, export_types in _discover_patients():
        summaries.append(
            EHRPatientSummary(
                patient_id=patient_id,
                patient_name=name_slug.replace("_", " ").title() if name_slug else None,
                export_types=export_types,
            )
        )
    return summaries


def get_patient_bundle(patient_id: str, export_type: str = "full") -> EHRPatientBundle | None:
    """Load one patient's EHR text for given export_type. Returns None if not found."""
    root = _ehr_root()
    for path in root.iterdir():
        if not path.is_dir() or not path.name.startswith("EHR-DATA_"):
            continue
        if not path.name.startswith(f"EHR-DATA_{patient_id}_"):
            continue
        # Find .txt file matching export_type (e.g. ..._full_20260201_....txt)
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
