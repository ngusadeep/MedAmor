# MedArmor

AI medical audit for **breast cancer screening compliance**. Compares patient EHR data to clinical guidelines (BI-RADS follow-up, screening intervals) and produces structured audit reports with findings, evidence, and corrective actions. Clinicians use the web UI to run and review audits; Celery Beat runs daily scheduled audits for due patients.

## Tech stack

| Layer   | Technology                    | Role |
|--------|-------------------------------|------|
| Frontend | React, Vite, shadcn           | Dashboard, jobs, reports, annotations. Served via nginx. |
| Backend  | FastAPI, Celery               | Auth, jobs (single/batch), audit reports, annotations. Workers run the audit pipeline; Beat runs scheduled audits. |
| Data     | PostgreSQL, Redis, ChromaDB   | Users, jobs, audit_reports, annotations; Celery broker; RAG over `docs/Medical_KB`. EHR from `ehr` service or local files. |
| AI       | MedGemma / Gemini / OpenAI    | Pluggable audit engine; LangGraph pipeline: fetch EHR → RAG → AI report. |

## Run the demo

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and
  [Docker Compose v2](https://docs.docker.com/compose/install/)
  - On Ubuntu/Debian: `sudo apt install docker-compose-v2`

### FHIR API

The demo uses a FHIR API at <http://localhost:8001>.

If you do not have a FHIR API server but wish to test, see the
instructions in [ehr/README.md](./ehr/README.md).

### Setup

1. Copy `.env.example` to `.env` and set required variables (at least `JWT_SECRET_KEY`; for AI set `AUDIT_AI_PROVIDER` and the matching keys: Gemini, OpenAI, or MedGemma/Vertex).
2. From project root:

   ```bash
   docker compose up --build
   ```

3. Open <http://localhost>
4. Sign in using "chief@medarmor.com" with the credentials in `backend/app/core/database.py` for that user.


#### Triggering audits

If you have a live FHIR server, it is possible to run the "cronjob" script to identify patients that trigger audits for those patients by the AI agent. This can be run using:

```bash
docker exec medaudit_backend python scripts/find_patients_due_for_audit.py --lastrun 2026-01-01T00:00:00Z --trigger --password chief123
```

Currently this is only run manually, but it could easily be adapted to run automatically at a set interval.


#### Pre-processed data

If you wish to load pre-processed results for the 2 failure cases, run `scripts/seed_demo_data.py`


## Development

- **Backend:** `backend/` — FastAPI; run with `uv run uvicorn main:app --reload` from `backend/` (see `backend/README.md`).
- **Frontend:** `frontend/` — Vite HMR; run with `pnpm dev` (see `frontend/README.md`).
- **EHR service:** `ehr/` — patient list and bundle API; in Docker it runs as a separate container.

## Architecture (default stack)

- **http://localhost** → nginx → frontend (static) and `/api` → backend (FastAPI).
- **Backend** talks to: PostgreSQL (medaudit_db), Redis (Celery), ChromaDB (RAG volume), EHR service (port 8001).
- **Worker / Beat** use the same image as the backend with different commands.

## Contributing

- **Branches:** `main` (production), `develop` (integration). Use `feature/frontend/...` or `feature/backend/...` for work.
- **Commits:** Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.).
