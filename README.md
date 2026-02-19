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
