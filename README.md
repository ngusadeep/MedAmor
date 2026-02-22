# MedAudit

### Project name
**MedAudit** — an AI-assisted medical audit system for **breast cancer screening compliance**. It compares patient EHR data against clinical guidelines (e.g. BI-RADS follow-up, screening intervals) and produces structured audit reports with findings, evidence, and corrective actions. The app serves clinicians and auditors via a web UI (dashboard, jobs, reports) and supports scheduled audits and human-in-the-loop annotations.

### Your team
| Name | Role / Contribution |
|------|---------------------|
| Charles Law | Team Lead; EHR server (patient list, bundle API, integrations). |
| Dr. Greg Russell | AI research, demo, Compliance and Governance. |
| Samwel Ngusa | Frontend (dashboard, jobs, reports, annotations UI). |
| Nazmus Sakib Ahmed | AI orchestration & Backend (pipeline, RAG, API, workers). |

### Problem statement
**Problem domain:** Ensuring breast cancer screening compliance at scale is hard. Guidelines (e.g. BI-RADS categories, follow-up intervals, recall timelines) must be applied consistently to each patient’s history. Manual review is slow, subjective, and easy to miss due-for-review patients or guideline gaps.

**Impact potential:** Automating compliance checks against a clinical knowledge base reduces missed follow-ups, standardizes audit criteria, and frees clinicians for higher-value work. Clear evidence trails and corrective actions improve accountability and quality of care.

### Overall solution
We use **HAI-DEF-capable models** (MedGemma, Gemini, or OpenAI) inside a **structured pipeline** so the AI acts as an audit assistant, not a black box:

- **RAG over clinical guidelines:** A vector store (ChromaDB) is indexed from `docs/Medical_KB` (clinical guidelines, BI-RADS, SOPs). For each audit, we **retrieve** relevant guideline chunks and pass them with the patient’s EHR text to the model. The model’s answers are grounded in this knowledge.
- **Orchestrated workflow:** A **LangGraph** pipeline runs in order: (1) fetch EHR data for the patient, (2) retrieve guidelines via RAG, (3) call the chosen AI to produce a **structured** report (compliant vs. gaps, evidence, corrective actions, next audit date). Same schema across MedGemma, Gemini, and OpenAI.
- **Human-in-the-loop:** Reports are stored in the app; auditors can attach **annotations** per finding (notes, overrides). Scheduled jobs (Celery Beat) run daily for patients due for review, keeping the human in the loop for verification and sign-off.

So the solution is “effective use of HAI-DEF models” by combining RAG, orchestration, and structured output with clinician review.

### Technical details
**Product feasibility** is shown by a single-command, self-contained stack that runs in Docker:

| Layer | Technology | Description |
|-------|-------------|-------------|
| Frontend | React + Vite | Dashboard, job creation, report list/detail, annotations. Served behind nginx. |
| Backend | FastAPI, Celery | Auth, jobs, batch jobs, audit reports, annotations, EHR proxy. Workers run the audit pipeline; Beat runs daily scheduled audits. |
| Data | PostgreSQL, Redis, ChromaDB | PostgreSQL: users, jobs, audit_reports, report_annotations. Redis: Celery broker. ChromaDB: RAG over `docs/Medical_KB`. EHR from optional service or local `ehr/` (FHIR-derived timelines). |
| AI | MedGemma / Gemini / OpenAI | One audit engine with pluggable providers. RAG retrieval and LangGraph (fetch EHR → RAG → AI) shared across providers. |

**Run the demo**

1. Copy `.env.example` to `.env` and set required variables (e.g. `JWT_SECRET_KEY`, and for AI: `AUDIT_AI_PROVIDER` with MedGemma, or Gemini/OpenAI keys).
2. From the project root:

```bash
docker compose up --build
```

| Resource | URL |
|----------|-----|
| App (UI) | http://localhost |
| API | http://localhost/api |


Sign up in the UI, create a breast cancer screening audit job (single patient or batch from the patient list), and view reports with findings, evidence, corrective actions, and annotations. See **WORKFLOW.md** for services, RAG ingest, and scheduled audit flow.


Optional platform/HAPI services (platform/test FHIR/EHR server) are behind profiles and do not start by default:

```bash
docker compose --profile platform --profile hapi up --build
```

## Create first user (MedAudit)

Use the in-app **Sign up** flow at <http://localhost>, or call the backend auth API to register. Then use **New screening audit job** to queue an audit (EHR + RAG + AI report).

---

# Operations

## Development with Hot Reloading

The development setup automatically reloads when you make changes:

- **Backend changes**: Edit files in `platform/backend/` — Flask will
  reload automatically
- **Frontend changes**: Edit files in `platform/ui/src/` — Vite HMR
  updates the browser instantly

## Stopping the Application

```bash
# Stop containers
sudo docker compose down

# Stop and remove data volumes
sudo docker compose down -v
```

See `platform/README.md` for detailed documentation on migrations, CLI
commands, API endpoints, and production deployment.

---

# Architecture

**MedAudit (default `docker compose up`):**

- Web UI: http://localhost (port 80, nginx)
- API: http://localhost/api
- PostgreSQL: medaudit_db (internal); ChromaDB persisted in backend volume

**With `--profile platform`:** Web UI and API at http://localhost:8080; DB at localhost:5432.

<!-- TODO: Fill in some technical information -->

---

# Contributing

## Branching Strategy

### Main Branches

- **`main`** — Production-ready code
- **`develop`** — Integration branch for new features

### Feature Branches

- Frontend contributors: `feature/frontend/[feature-name]`
- Backend contributors: `feature/backend/[feature-name]`

## Workflow

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/frontend/your-feature-name
   # or
   git checkout -b feature/backend/your-feature-name
   ```

2. **Make Changes**
   - Frontend: Work in `/frontend` directory
   - Backend: Work in `/backend` directory

3. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: your descriptive commit message"
   git push origin feature/your-branch-name
   ```

4. **Create Pull Request**
   - Target branch: `develop`
   - Add reviewers
   - Ensure CI passes

5. **Merge Process**
   - PR → `develop` (after review)
   - `develop` → `main` (release-ready)

## Getting Started

1. Clone the repository
2. Choose your component (frontend/backend)
3. Follow component-specific setup instructions
4. Create your feature branch from `develop`

## Commit Convention
