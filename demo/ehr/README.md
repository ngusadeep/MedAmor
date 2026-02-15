# EHR — Patient data for MedAudit backend

EHR data is **served by a FastAPI app** (`server.py`). The **backend** calls this service to list patients and get patient bundle by ID; the backend then returns that data to the **frontend**.

## Layout

| Path | Purpose |
|------|--------|
| **fhir/** | FHIR R4 bundle JSONs (for HAPI upload and for building text exports). |
| **patients/** | Text timelines per patient (`<id>/full.txt`). **EHR service** reads these. |
| **server.py** | FastAPI app: `GET /patients`, `GET /patients/{patient_id}?export_type=full`. Same response shape as backend schemas. |
| **build_patient_exports.py** | Converts `fhir/*.json` → `patients/<id>/full.txt`. Run once (or after adding FHIR data). |
| **upload_fhir.sh** | Uploads `fhir/` to HAPI FHIR server (optional). |
| **docker-compose.yml** | HAPI FHIR + Postgres (optional). |
| **Dockerfile** | Builds the EHR FastAPI service (used by demo docker-compose). |

## Flow

1. **Frontend** asks backend for patients or for one patient by ID.
2. **Backend** calls **EHR service** (`EHR_SERVICE_URL`, e.g. `http://ehr:8000`): `GET /patients`, `GET /patients/{id}`.
3. **EHR service** reads from `patients/` (mounted at `/data` in Docker) and returns JSON (list or bundle).

## Generate patient text (before first run)

From `ehr`:

```bash
python build_patient_exports.py
```

This fills `patients/<id>/full.txt` from `fhir/*.json`. The EHR service serves these.

## Run EHR service alone (e.g. local dev)

```bash
cd ehr
EHR_DATA_PATH=. python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
# Or: python server.py
```

Backend then needs `EHR_SERVICE_URL=http://localhost:8000` to use this service.
