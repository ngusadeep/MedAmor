# MedAudit — Step-by-Step Project Plan

**AI-Powered Clinical Audit Platform (RAG + MedGemma)**  
Hackathon: Med Gemma Impact Challenge | Full working MVP

---

## 1. Current State

| Area | Status |
|------|--------|
| **frontend/** | React + Vite + shadcn; auth pages, dashboard, tasks table, chat, calendar. **To adapt:** dashboard → audits, add manual review form, wire one login flow. |
| **backend/** | Minimal FastAPI (health + root). **To add:** DB, RAG, Celery, MedGemma, audit API. |
| **docs/** | PROJECT_PLAN.md + **Medical_KB/** (Documentation, SOPs, User_Manuals, FAQs) with sample content. |
| **EHR data** | Sample in repo: `EHR-DATA_51674_mrs_elinore878_barton704_/` — .txt timeline exports (full, handoff_*, imaging_*). |
| **Kaggle** | Writeup + video; evaluation criteria documented below. |

---

## 2. Decisions (locked)

| Decision | Choice |
|----------|--------|
| **EHR for MVP** | Mock API first; sample data in repo. Backend accepts patient bundle (EHR text + optional image refs). |
| **Knowledge base** | Check docs; add sample content where missing. All sample knowledge — can be updated. |
| **MedGemma** | **Hugging Face Inference API** (Inference Endpoints). |
| **Auth** | **Real auth** with JWT + backend. |
| **Deployment** | **Docker Compose** first; Kubernetes later. |
| **Kaggle submission** | Single Writeup (≤3 pages) + video (≤3 min); public code repo; optional demo + HF model tracing. |

---

## 2b. EHR Data Format (from sample)

- **Location:** Root folder `EHR-DATA_{patient_id}_{patient_name_slug}_/`.
- **Files:** `.txt` exports with header:
  - `Patient ID`, `Patient Name`, `Export Type`, `Generated` (ISO datetime).
- **Export types:** `full`, `handoff_complete`, `handoff_minimal`, `imaging_complete`, `imaging_minimal`.
- **Structure:** `PATIENT INFORMATION` block (demographics, contact) then `CHRONOLOGICAL TIMELINE` with date blocks containing:
  - **VISIT** (procedure, provider, location, duration, reason).
  - **CONDITION** (finding/disorder, active/resolved).
  - **DIAGNOSTIC REPORT** (History and physical note, content preview).
  - **DOCUMENT** (status: superseded/current).
  - **OBSERVATION** (vitals, labs, scores).
  - **PROCEDURE**, **CARE PLAN**, **IMMUNIZATION**, **MEDICATION**, **IMAGING STUDY** (when imaging_complete/minimal).
- **Use:** Backend parses or accepts raw text; mock API can serve these files by patient_id / export_type. Generate ~5 sample patients from this schema when needed.

---

## 2c. Kaggle Evaluation & Submission

- **Submission:** One Kaggle Writeup (attached to competition page); ≤3 pages; required video ≤3 min; required public code repo. Optional: live demo, open-weight HF model tracing to HAI-DEF.
- **Writeup template:** Project name → Team → Problem statement → Overall solution (HAI-DEF use) → Technical details (product feasibility).
- **Evaluation criteria:**

| Criteria | Weight | Focus |
|----------|--------|--------|
| Effective use of HAI-DEF models | 20% | MedGemma/HAI-DEF used appropriately; use is mandatory. |
| Problem domain | 15% | Importance, clarity, unmet need, user journey. |
| Impact potential | 15% | Real or anticipated impact. |
| Product feasibility | 20% | Technical docs, stack, deployment, use in practice. |
| Execution and communication | 30% | Video clarity, write-up completeness, code quality. |

---

## 3. Phased Plan (we execute step by step)

### Phase 1 — Foundation (backend + data shape)

- **1.1** Backend: Postgres + SQLAlchemy (or similar) for **jobs** and **audit reports** (schema matching your payload: job_id, patient_id, status, findings, evidence, etc.).
- **1.2** Define **EHR input schema** (placeholder until you give sample). Backend API to accept “patient bundle” (EHR + optional images) for one audit run.
- **1.3** Knowledge base: create `docs/Medical_KB/` with folder structure (Documentation, SOPs, User_Manuals, FAQs). Add a few **example markdown** docs so RAG has content.
- **1.4** (Optional) If HAPI FHIR is in scope: add Docker service for HAPI FHIR and a thin “EHR adapter” that maps FHIR → our internal EHR schema.

**Deliverable:** Backend can store jobs/reports; KB on disk; clear EHR schema (or FHIR mapping).

---

### Phase 2 — RAG pipeline

- **2.1** Chunking: 384–768 token chunks, clinical-boundary aware; metadata (patient_id, document_name, document_type, record_type, modality, date, source).
- **2.2** Embeddings: ClinicalBERT for EHR text, GPT-3 (or chosen) for KB; store in **Qdrant** (Docker).
- **2.3** Indexing: script to embed KB markdown and (later) EHR snippets into Qdrant with metadata filters.
- **2.4** Retrieval API: given patient context, return relevant KB + EHR chunks for the audit engine.

**Deliverable:** Qdrant up; KB indexed; retrieval endpoint that returns context for a patient.

---

### Phase 3 — Audit engine (MedGemma)

- **3.1** Integrate **MedGemma** (local or Hugging Face Inference): multimodal (text + images), with **system prompt** that enforces: no diagnosis, cite evidence, flag mismatches.
- **3.2** Audit orchestration: input = patient EHR + retrieved RAG context + optional images → one structured output (executive summary, findings, risk, corrective actions, explainability).
- **3.3** Map model output to your **structured payload** (job_id, patient_id, status NO_FINDINGS / FINDING_PRESENT, findings with category, description, responsible doctor, urgency, evidence snippets).
- **3.4** Persist result to Postgres (audit reports table) and link to job.

**Deliverable:** One “run audit for this patient” path from API to stored report.

---

### Phase 4 — Jobs and scheduling (Celery)

- **4.1** Redis (or RabbitMQ) + Celery: define audit task (receives job_id / patient_id, calls RAG + MedGemma, saves report).
- **4.2** API: “Create job” (manual trigger) creates DB job and enqueues Celery task.
- **4.3** Celery Beat: simple hourly cron for “new or expected follow-ups” (e.g. query jobs due or new patients).
- **4.4** Optional: batch endpoint for onboarding (e.g. “run audits for last 2 years” split into chunks) for parallel processing.

**Deliverable:** Manual and scheduled audit jobs; results in DB and visible via API.

---

### Phase 5 — Frontend (UI)

- **5.1** **Login** → Dashboard: use one of the existing sign-in pages; wire to backend auth if we do real JWT, else mock.
- **5.2** **Dashboard** = main view: table of **historical audits** (columns: e.g. job id, patient id, date, status [No Findings / Findings Present], risk level). Data from backend API.
- **5.3** **Manual review**: form to trigger audit (e.g. select patient or enter patient id), submit → create job via API, show “pending” then refresh when job completes (polling or simple refresh).
- **5.4** **Audit detail view**: click row → show full payload (executive summary, findings, evidence, suggested actions).
- **5.5** (If time) Link “expected follow-up / next AI audit” from payload to dashboard.

**Deliverable:** Login → Dashboard (audits table) → Trigger audit → Detail view.

---

### Phase 6 — Sample data and evaluation

- **6.1** When you provide **sample EHR format** (and optionally sample images): we define ingestion (and if needed, FHIR adapter), then generate **~5 sample patient records** and run full pipeline.
- **6.2** Align output with **Kaggle evaluation**: once you share metrics/submission format, we add any scoring script or export (e.g. CSV/JSON for submission) and tune prompts/output shape if needed.

**Deliverable:** Reproducible run on 5 samples; output compatible with competition.

---

### Phase 7 — Deployment and polish

- **7.1** Docker Compose: frontend, backend, Postgres, Redis, Qdrant, Celery worker, Celery Beat. Optional: HAPI FHIR, MedGemma service.
- **7.2** Env vars: document in `.env.example` (API URLs, DB, Redis, HF token, etc.).
- **7.3** Guardrails and compliance: audit logs for runs, no diagnosis in prompts, PHI handling (e.g. no logging of raw PHI).

**Deliverable:** One-command run for judges; README with setup and how to trigger an audit.

---

## 4. Suggested order of execution

We can do:

1. **Phase 1** (foundation) first — then you can add real KB docs and we can plug in your EHR sample when ready.  
2. Then **Phase 2** (RAG) and **Phase 3** (MedGemma) so that “run one audit” works.  
3. Then **Phase 4** (Celery) and **Phase 5** (UI) so the platform is full-stack.  
4. **Phase 6** when you have sample data and eval criteria; **Phase 7** for Docker and README.

---

## 5. What I need from you next

- Answers (even short) to the **clarifications** in §2.  
- When ready: **sample EHR structure** (and sample image references if any) → we’ll add ~5 samples and wire ingestion.  
- When you can open the Kaggle page: **evaluation metrics and submission format**.

After you reply, we can start with **Phase 1** (e.g. Postgres schema for jobs/reports + `docs/Medical_KB/` structure + example KB files and EHR schema placeholder).
