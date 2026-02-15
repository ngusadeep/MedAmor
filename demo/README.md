# MedAudit Demo

Self-contained **Breast Cancer Screening Audit** demo: **frontend** (UI) → **backend** (API + audit) → **EHR service** (patient data).

## Data flow

- **Frontend** requests patient list or patient by ID from the **backend** (`/api/ehr/patients`, `/api/ehr/patients/{id}`).
- **Backend** calls the **EHR FastAPI service** (same schema: list + get by patient_id), then returns the response to the frontend.
- **EHR service** reads from `ehr/patients/` (text timelines). Run `ehr/build_patient_exports.py` once to generate from `ehr/fhir/`.

## Contents

| Folder        | Role |
|---------------|------|
| **backend**  | FastAPI, Celery, RAG; exposes `/api/ehr/patients` and forwards to EHR service. |
| **frontend** | React + Vite UI (dashboard, jobs, reports). |
| **ehr**      | FHIR bundles, `patients/` text exports, **EHR FastAPI service** (server.py) that serves them. |
| **docs/Medical_KB** | Clinical guidelines (RAG). |
| **nginx**    | Reverse proxy: /api → backend, / → frontend. |

## Run the demo

1. **Env:** Copy `.env.example` to `.env` and set values (e.g. `JWT_SECRET_KEY`). Compose and the backend (when run from `demo/backend`) use `demo/.env`.
2. From this directory (`demo/`):

```bash
docker compose up --build
```

- **App (UI):** http://localhost  
- **API:** http://localhost/api  
- **EHR service (internal):** http://localhost:8001 (list/get patients; backend uses http://ehr:8000)

Sign up in the UI, then create a **breast cancer screening audit job** using a patient ID from the patient list (backend gets the list from the EHR service).

## Optional: run from repo root

If you prefer to keep backend/frontend at the repo root and only use this compose:

```bash
cd /path/to/MedAudit
docker compose -f demo/docker-compose.yml --project-directory demo up --build
```

You’ll need to adjust build contexts in `demo/docker-compose.yml` to `../backend`, `../frontend`, etc., or run from `demo` as above.
