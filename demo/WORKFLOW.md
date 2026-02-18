# Demo workflow

How the **Breast Cancer Screening Audit** demo runs end-to-end.

---

## 1. Services (Docker)

| Service            | Role | Port (host) | Used by |
|--------------------|------|-------------|--------|
| **nginx**          | Reverse proxy: `/` → frontend, `/api` → backend | 80 | Browser |
| **medaudit_frontend** | React app (dashboard, jobs, reports, annotations) | (via nginx) | User |
| **medaudit_backend**  | FastAPI: auth, jobs, batch jobs, audit-reports, annotations, **ehr**, RAG | (via nginx /api) | Frontend, worker |
| **medaudit_worker**   | Celery worker: runs audit job (EHR + RAG + AI → report) | — | Backend (enqueue) |
| **medaudit_beat**     | Celery Beat: daily CRON to create scheduled audit jobs | — | Redis (schedule) |
| **ehr**            | FastAPI: serves patient list + patient bundle (ehr_text) | 8001 (optional) | Backend |
| **medaudit_db**    | PostgreSQL: users, jobs, audit_reports, report_annotations | 5434 | Backend, worker |
| **redis**          | Celery broker + result backend | 6379 | Backend, worker, beat |
| **chroma_data**    | Volume: RAG vector store (ChromaDB) | — | Backend, worker |
| **hapi_db** / **hapi_fhir** | Optional FHIR server | 5433, 9080 | (optional upload) |

**Run:** `docker compose up --build` from `demo/`.  
**App:** http://localhost (nginx). **API:** http://localhost/api.

---

## 2. User flow (high level)

1. **Sign up / Sign in** (frontend → backend `/api/auth/*`).
2. **Dashboard** – stats from backend (jobs, reports).
3. **Audit Jobs** – list jobs (`GET /api/jobs`), **Create job** with a **patient ID** or **batch** (multi-select patients).
4. **Backend** creates job(s) in DB and enqueues **Celery** `run_audit_task(job_id)` for each.
5. **Worker** runs the audit (see §4), saves the report, sets job to COMPLETED (or FAILED). Job status is **IN_PROGRESS** while running.
6. **Reports** – list reports (`GET /api/audit-reports`), open a report to see findings, evidence, corrective actions, **next audit date**, and **annotations (human-in-the-loop)**.
7. **Annotations** – on report detail: list annotations per finding, add note (finding index + note) via `POST /api/audit-reports/{id}/annotations`.

**Patients** – list (`GET /api/patients`) is enriched from the latest audit report per patient: **last_audit_date**, **next_audit_date**, **status** (never_audited, due_for_review, compliant, needs_attention), **risk_level**. Due-for-review (`GET /api/patients/due-for-review`) returns only patients due (next_audit_date ≤ today or never audited) and without a pending job. Patient IDs come from the **EHR service** (or disk when `EHR_SERVICE_URL` is not set).

---

## 3. Knowledge base (RAG) – ChromaDB

- **Source:** `docs/Medical_KB` (or `MEDICAL_KB_PATH`). Markdown under Documentation, SOPs, User_Manuals, FAQs, Clinical_Guidelines.
- **Vector DB:** **ChromaDB** (persisted in `CHROMA_PERSIST_DIR`).
- **Ingest:** On backend startup, `rag.ensure_indexed()` runs. It compares current doc paths + mtimes to a **manifest** (`chroma_persist_dir/kb_index_manifest.json`). **Only if there are new or changed files** does it re-run `index_kb()`; otherwise ingest is skipped.
- **Retrieve:** Audit engine calls `rag.retrieve(query)` for breast cancer screening context before calling the AI.

---

## 4. Audit job flow (create → report)

1. **User** submits “New audit job” with one **patient ID** or selects multiple patients (batch).
2. **Frontend** → `POST /api/jobs` (single) or `POST /api/jobs/batch` with `{ patient_ids }`.
3. **Backend** creates **Job**(s) (status PENDING), then calls `run_audit_task.delay(job.id)` for each.
4. **Celery worker**:
   - Loads job from DB.
   - Sets job status **IN_PROGRESS**; updates task state (PROCESSING + meta: stage).
   - Calls **audit engine** `run_audit(...)` which uses **LangGraph orchestrator**:
     - **fetch_ehr_data:** `get_patient_bundle(patient_id)` → EHR service (or disk) → `ehr_text`.
     - **retrieve_guidelines:** `rag.retrieve(query)` (ChromaDB) → guideline chunks.
     - **generate_audit_report:** **audit_ai** (MedGemma / Gemini / OpenAI) → compliant, gaps, evidence; mapped to report schema.
   - Builds **AuditReport**, saves to DB.
   - Sets job status COMPLETED (or FAILED on error).
5. **Frontend** can poll job by id or list reports; **report detail** page shows findings, evidence, corrective actions, next audit date, and annotations.

---

## 5. Scheduled audits (CRON – Celery Beat)

- **Celery Beat** runs in a separate container (`medaudit_beat`), schedule: **daily at 06:00 UTC** (every 24h).
- Task: **`create_scheduled_audit_jobs`** (full workflow per patient).
- Logic:
  - **Due for review:** patients with no report yet, or whose latest report has `next_audit_date` is None or `next_audit_date <= today`.
  - Exclude patients that already have a PENDING or IN_PROGRESS job.
  - For each due patient, create one job with `triggered_by="scheduled"` and enqueue `run_audit_task.delay(job.id)`.
  - Each job runs the full RAG/orchestrator workflow; the resulting report stores **review date** (report `created_at`) and **next_audit_date** (from AI). Patient list and “due” counts are derived from latest report per patient.

---

## 6. AI providers

| Provider   | Env / config | Notes |
|-----------|--------------|--------|
| **MedGemma** | `AUDIT_AI_PROVIDER=medgemma` | Local / container model. |
| **Gemini**   | `AUDIT_AI_PROVIDER=gemini`, `GOOGLE_API_KEY`, `GEMINI_MODEL` | Google Generative AI. |
| **OpenAI**   | `AUDIT_AI_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_AUDIT_MODEL` | Chat completions. |

Same structured output (status, findings, evidence, etc.) for all providers.

---

## 7. Summary diagram

```
[User] → [Frontend :80] → [nginx] → /api → [Backend]
                                          |
        ←─────────────────────────────────+
        |                    |                    |
        |  /api/ehr/*        |  /api/jobs         |  /api/audit-reports/…/annotations
        v                    |  /api/jobs/batch  v
   [EHR service :8000]   [Redis] ←——————— [Celery Beat] (daily)
        |                    |
        |                    v
        |                [Celery worker] → run_audit → EHR + RAG (ChromaDB) + AI
        |                    |
        |                    v
        |                [PostgreSQL] (jobs, audit_reports, report_annotations)
        |                [ChromaDB] (RAG)
```

---

## 8. Implemented vs planned

| Feature | Status |
|--------|--------|
| Single job create | ✅ Implemented |
| Batch job create (API + frontend multi-select) | ✅ Implemented |
| Job status IN_PROGRESS | ✅ Implemented |
| RAG from docs → ChromaDB, incremental ingest | ✅ Implemented |
| AI: MedGemma, Gemini, OpenAI | ✅ Implemented |
| Human-in-the-loop annotations (model, API, frontend) | ✅ Implemented |
| CRON: Celery Beat + create_scheduled_audit_jobs | ✅ Implemented |
| LangGraph orchestrator (fetch → RAG → AI) | ✅ Implemented |
| Queue stats `GET /api/jobs/queue/stats` | ✅ Implemented |
| Task status `GET /api/jobs/task/{task_id}/status` | ✅ Implemented |
| Notifications (e.g. email on report) | ⏳ Planned |
