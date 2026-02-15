"""EHR data service: FastAPI app that serves patient list and patient bundle (ehr_text).

Response format matches backend schemas EHRPatientSummary and EHRPatientBundle
so the backend can proxy requests from the frontend to this service.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Data root: same layout as ehr/ (patients/<id>/full.txt). In Docker mount ehr at /data.
_def = os.environ.get("EHR_DATA_PATH", "/data")
DATA_ROOT = Path(_def) if Path(_def).is_absolute() else Path(__file__).resolve().parent / _def


class EHRPatientSummary(BaseModel):
    patient_id: str
    patient_name: str | None = None
    export_types: list[str]


class EHRPatientBundle(BaseModel):
    patient_id: str
    export_type: str = "full"
    ehr_text: str
    image_refs: list[str] | None = None


app = FastAPI(title="EHR Data Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _list_patients() -> list[EHRPatientSummary]:
    patients_dir = DATA_ROOT / "patients"
    if not patients_dir.is_dir():
        return []
    out = []
    for path in sorted(patients_dir.iterdir()):
        if not path.is_dir():
            continue
        patient_id = path.name
        export_types = [f.stem for f in path.iterdir() if f.is_file() and f.suffix == ".txt"]
        if export_types:
            out.append(
                EHRPatientSummary(
                    patient_id=patient_id,
                    patient_name=None,
                    export_types=sorted(set(export_types)),
                )
            )
    return out


def _get_patient_bundle(patient_id: str, export_type: str = "full") -> EHRPatientBundle | None:
    patients_dir = DATA_ROOT / "patients" / patient_id
    if not patients_dir.is_dir():
        return None
    f = patients_dir / f"{export_type}.txt"
    if not f.is_file():
        return None
    text = f.read_text(encoding="utf-8", errors="replace")
    return EHRPatientBundle(
        patient_id=patient_id,
        export_type=export_type,
        ehr_text=text,
        image_refs=None,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/patients", response_model=list[EHRPatientSummary])
def list_patients():
    """List all patients (ids and export_types). Backend calls this and forwards to frontend."""
    return _list_patients()


@app.get("/patients/{patient_id}", response_model=EHRPatientBundle)
def get_patient(patient_id: str, export_type: str = "full"):
    """Get one patient's EHR text. Backend calls this and forwards to frontend."""
    bundle = _get_patient_bundle(patient_id, export_type)
    if not bundle:
        raise HTTPException(
            status_code=404,
            detail=f"EHR not found for patient_id={patient_id}, export_type={export_type}",
        )
    return bundle


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
