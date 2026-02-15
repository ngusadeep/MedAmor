# MedAudit Backend

FastAPI backend for the MedAudit **Breast Cancer Screening Audit** system (EHR + RAG + AI reports).

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   # or: pip install -e .
   ```

2. **Environment setup:**
   ```bash
   cp .env.example .env
   # Edit .env if needed (PostgreSQL required; project root for EHR mock)
   ```

3. **Run the server:**
   ```bash
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   # or: python main.py
   ```

## API Documentation

Once running:
- **OpenAPI (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health:** http://localhost:8000/health

## API (Breast Cancer Screening)

- **POST /jobs** — Create audit job (body: `patient_id`, optional `audit_type` default `breast_cancer_screening`, `export_type`, `triggered_by`).
- **GET /jobs** — List jobs (query: `patient_id`, `status`).
- **GET /jobs/{job_id}** — Get one job.
- **GET /audit-reports** — List audit reports (query: `job_id`, `patient_id`).
- **GET /audit-reports/{report_id}** — Get one report.
- **GET /audit-reports/by-job/{job_id}** — Get report for a job.
- **GET /ehr/patients** — List patients in mock EHR (EHR-DATA_* folders).
- **GET /ehr/patients/{patient_id}** — Get patient EHR text (query: `export_type`, default `full`).

## Database

Tables are created on startup via `init_db()`. If you have an **existing** database from before the `audit_type` column was added, run:

```sql
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS audit_type VARCHAR(64) NOT NULL DEFAULT 'breast_cancer_screening';
```

## Development

- Python 3.12+
- FastAPI, Pydantic v2, Pydantic Settings
- SQLAlchemy 2, PostgreSQL
- Uvicorn ASGI server

## Project Structure

```
backend/
├── app/
│   ├── core/           # config, database
│   ├── models/         # Job, AuditReport
│   ├── schemas/        # Pydantic request/response, EHR
│   ├── routers/       # jobs, audit_reports, ehr
│   └── services/      # ehr_mock
├── main.py
├── pyproject.toml
├── .env.example
└── README.md
```