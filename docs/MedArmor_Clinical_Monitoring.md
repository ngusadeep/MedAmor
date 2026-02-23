## MedArmor: Clinical Monitoring

## Executive Summary

MedArmor is an AI-driven monitoring framework that audits EHRs against clinical guidelines in near real-time to close care gaps. Our first implementation focuses on breast cancer screening, automatically identifying patients with abnormal results who have missed critical follow-up. By automating these audits, MedArmor reduces provider liability and allows for early intervention to reduce patient harm.

## MedArmor Team

- **Nazmus Sakib Ahmed**: AI Researcher and lecturer at BRAC University. Led AI Agent Development and System Design for MedArmor.
- **Charles Law (Team Lead)**: Engineer who oversaw the implementation and deployment of a pioneering autonomous AI (EyeArt) in various healthcare systems. Led product/idea discussion and EHR integration for MedArmor.
- **Samwel Ngusa**: AI and Backend Engineer and Researcher building production grade AI Agents and RAG pipelines that solve real-world problems. Led frontend UI work and system component integration for MedArmor.
- **Greg Russell**: Oversaw clinical research for the development of EyeArt, a pioneering autonomous AI for ophthalmology. Helped guide product discussion and idea selection while providing clinical feedback for MedArmor.

## Problem Statement

### Clinical Problem

Medical audits are difficult and time-consuming, requiring specialized expertise that is often needed for more immediate clinical demands. Because of the high resource cost, audits are performed less often than they should be and typically occur only after patient harm has already occurred, at which point the damage may be irreversible and the healthcare system may face legal liability.

The scale of preventable issues is significant. More than 35% of screenings with abnormal findings do not receive follow-up [1], placing patients at substantial risk. For breast screening specifically, 68.4% did not have a follow up within 60 days of an abnormal finding [2]. From a business perspective, 47% of malpractice claims mention provider-provider communication and failure to follow up on care [3]. These gaps lead to reduced patient safety while increasing costs.

## Impact

MedArmor leverages the MedGemma AI model to dramatically reduce the cost of medical audits and increase visibility into care delivery. Rather than auditing a small subset of cases retrospectively, every patient can be reviewed continuously. Potential issues can be identified earlier, enabling timely intervention and reducing the likelihood and severity of patient harm.

MedArmor is designed for easy adoption:

- It is a safety net for providers, helping reduce malpractice risk.
- It is **read-only** with respect to upstream systems.
- It is designed to run in a hospital network with a pluggable EHR connector and pluggable AI runtime.

## Overall Solution

### System Architecture

MedArmor is implemented as a small set of composable services:

- **Platform (Backend)**: FastAPI API for jobs, reports, patients, auth, RAG tools, and transcription.
- **Platform (Frontend)**: React + Vite dashboard for initiating audits, viewing job/report status, and annotating findings.
- **EHR Data Service**: A separate FastAPI service that serves patient lists and per-patient “bundle” exports. In the demo, it is backed by a PostgreSQL table populated from FHIR JSON bundles.
- **Queue + Scheduler**: Celery worker(s) for asynchronous execution and Celery Beat for scheduled audits.
- **AI Orchestrator**: A LangGraph state machine that runs fetch → (optional extraction) → guideline retrieval → structured audit generation.
- **Knowledge Base**: Markdown guidelines under `docs/Medical_KB/`, indexed into ChromaDB for retrieval-augmented generation (RAG).

### Components and Workflow (as implemented)

1. **Job creation**
   - Users create an audit job via the UI or API (`POST /api/jobs`, or `/api/jobs/batch`).
   - Each job stores: patient id, audit type, optional sensitivity, and optional per-job model/extraction overrides.

2. **Asynchronous execution**
   - The backend enqueues `run_audit_task` to Celery (Redis broker).
   - The worker loads the job record, runs the audit pipeline, persists a report, and updates job status.

3. **EHR fetch**
   - The audit pipeline loads the patient timeline text from:
     - an **EHR service** (`EHR_SERVICE_URL`), or
     - local demo files (`patients/<patient_id>/full.txt` or legacy `EHR-DATA_*` folders).

4. **Guidelines retrieval**
   - The orchestrator retrieves guideline context in one of two modes:
     - **RAG** (default): retrieve the top \(k=5\) chunks from ChromaDB based on an audit-type query.
     - **Full-load**: load the entire KB markdown into the prompt (useful when there’s a single guideline file and you want no embeddings).

5. **AI audit**
   - The AI step generates a structured audit result (JSON) grounded in the retrieved guideline context.
   - Sensitivity can be set globally or per-job to tune “flag everything vs only critical gaps.”

6. **Persistence + review**
   - The report is stored in PostgreSQL and served via `GET /api/audit-reports…`.
   - Reviewers can attach human notes to specific findings (human-in-the-loop) via report annotations.

7. **Scheduled audits**
   - Celery Beat runs daily and creates jobs for patients due for review (never audited, or next_audit_date is due).

## Technical Details (Implementation)

### Platform (Backend)

- **Framework**: FastAPI (Python 3.12+).
- **Database**: PostgreSQL via SQLAlchemy 2.
- **Auth**: JWT-based auth (cookie or Bearer token). Endpoints are protected, and job creation requires a “Chief Doctor” role in the demo auth model.
- **Core domain objects**:
  - `jobs`: audit jobs (pending → in_progress → completed/failed)
  - `audit_reports`: structured audit output linked 1:1 to a job
  - `report_annotations`: reviewer notes on a specific finding index (stored separately from AI output)
- **API surface (high level)**:
  - Jobs: create/list/get + queue inspection
  - Audit reports: list/get/by-job + export + annotations
  - Patients: list/stats/due-for-review (computed from EHR + latest reports)
  - EHR proxy endpoints: list patients + get patient bundle/detail
  - RAG utility endpoints (for KB indexing/retrieval)
  - Transcription endpoint for voice input

### EHR Integration (FHIR-backed demo + pluggable connector)

MedArmor supports two practical integration patterns:

- **External EHR service mode (recommended for real integration)**:
  - Set `EHR_SERVICE_URL` and the backend uses a small HTTP client to call:
    - `GET /patients/` (list)
    - `GET /patients/{patient_id}/detail`
    - `GET /patients/{patient_id}` (bundle export; in the demo only `export_type=full` is supported)
  - This keeps platform logic independent of the upstream EHR vendor and allows different connectors.

- **Local demo mode (no EHR service configured)**:
  - The backend reads timeline exports from disk under:
    - `patients/<patient_id>/<export_type>.txt` (preferred), or
    - legacy `EHR-DATA_*` folders.

#### FHIR → “LLM-friendly” timeline export

The demo EHR service stores a raw FHIR R4 bundle per patient (JSON) and generates a cached, chronological narrative (“timeline”) on first request.

- **Import**: `ehr/migrate_from_fhir.py` scans `ehr/fhir/*.json`, extracts demographics from the `Patient` resource, and stores:
  - patient id + demographics
  - the raw FHIR bundle JSON
  - an empty `timeline_cache` (lazy generation)
- **Lazy timeline generation**: when a patient bundle is requested and `timeline_cache` is missing, it is generated from the stored FHIR JSON.
- **Timeline conversion**:
  - Converts many FHIR resource types (Encounter, Observation, DiagnosticReport, Condition, Procedure, ImagingStudy, etc.) into dated events.
  - Sorts events chronologically.
  - Outputs a readable narrative that privileges clinical signal over admin/structural fields.
  - Optionally includes cost-related “Claim” events (useful for future cost-quality lenses).

This export is the “patient_summary” input to the audit pipeline in one-pass mode, and the raw text input to the extraction pass in two-pass mode.

### Orchestration (LangGraph state machine)

The audit execution path is implemented as a LangGraph `StateGraph` (deterministic node order):

- **Fetch EHR data**: obtain the timeline export for the patient.
- **(Optional) Pass 1 extraction**: in two-pass modes, run an extraction prompt to produce a compact clinical summary tailored to the audit type.
- **Retrieve guideline context**: either RAG retrieval from ChromaDB or full KB load.
- **Generate structured audit report**: call the configured model provider and force a strict JSON return format.

This structure makes it easy to add additional audit types as new prompt templates + new guideline retrieval queries.

### RAG / Knowledge Base

- **Knowledge base format**: markdown files under `docs/Medical_KB/…` (including `Clinical_Guidelines/`).
- **Vector store**: ChromaDB (persistent directory).
- **Indexing**:
  - On backend startup, the KB is indexed **only if docs changed** (tracked via a simple manifest of file mtimes).
  - Text is chunked using a recursive splitter (default chunk size ~2048 chars, overlap ~256).
- **Embedding providers** (pluggable):
  - **FastEmbed** (default; no API key): `sentence-transformers/all-MiniLM-L6-v2`
  - **OpenAI** embeddings (requires API key)
  - **MedSigLIP text encoder**: supported, but requires very small chunks due to a 64-token context limit (useful groundwork for future multimodal retrieval)

The orchestrator uses RAG results as grounded “guideline context” in the prompt, and also returns sources for traceability.

### AI Agent (MedGemma-first, provider-pluggable)

MedArmor exposes a single “audit AI” interface with multiple interchangeable backends:

- **MedGemma** (default provider)
  - **Hugging Face Inference API** backend (configure `HF_TOKEN` + `HF_MEDGEMMA_ENDPOINT`)
  - **Vertex AI hosted endpoint** backend (configure project/location/endpoint id)
- **Gemini** backend (configure `GOOGLE_API_KEY` + `GEMINI_MODEL`)
- **OpenAI** backend (configure `OPENAI_API_KEY` + `OPENAI_AUDIT_MODEL`)

#### One-pass vs two-pass

- **One-pass**: the orchestrator sends the timeline export + retrieved guideline context directly to the model.
- **Two-pass**: a first model call performs **extraction** (audit-type specific), producing a focused clinical summary; a second call performs the actual guideline audit using the extracted summary.
  - Extraction can be run with either MedGemma or Gemini (configurable).

#### Sensitivity control (global + per-job)

MedArmor supports “sensitivity” as a product control, not a model hack:

- The prompt includes a sensitivity directive (LOW/MEDIUM/HIGH) to influence how aggressively gaps are flagged.
- The audit engine then applies a **post-model filter** for active findings/evidence using a threshold derived from sensitivity:
  - higher sensitivity → lower confidence threshold → more findings retained
  - lower sensitivity → higher threshold → fewer findings retained

#### Structured output contract

The orchestrator forces the model to return strict JSON with:

- `compliant`: boolean
- `gaps`: list of currently outstanding gaps
- `close_calls`: items that were resolved but completed late (quality improvement tracking)
- `evidence`: `{ guideline, violation, confidence, harm_severity }[]`

The platform stores a normalized report schema:

- `status`: `NO_FINDINGS` or `FINDING_PRESENT`
- `risk_level`: low/medium/high
- `executive_summary`
- `findings[]`, `evidence[]`, `corrective_actions[]`
- `next_audit_date` (reserved for future auto-rescheduling logic)

### Human-in-the-loop review (annotations)

The platform supports clinician review without overwriting the AI output:

- Reviewers can attach notes to a particular finding index on a report.
- Notes are stored in a separate table and served via an annotations endpoint.
- This pattern supports accountability and iterative workflow refinement (e.g., “false positive due to missing external imaging record”).

### Voice input (clinical ASR)

The platform includes a transcription endpoint intended for fast reviewer notes:

- `POST /api/transcribe` accepts multipart audio uploads (e.g. browser MediaRecorder `audio/webm`).
- Providers (pluggable):
  - MedASR via Hugging Face Inference API
  - MedASR local inference via `transformers` pipeline (CPU/GPU), with decoding via `librosa` + `ffmpeg`
  - Deepgram Nova medical model

### Scheduling and queueing

- **Queue**: Celery, brokered by Redis.
- **Workers**: process audit jobs asynchronously; the API remains responsive.
- **Scheduler**: Celery Beat runs daily and creates jobs for patients due for review:
  - “due” = never audited, or latest `next_audit_date` is missing or in the past
  - excludes patients that already have a pending/in-progress job

### Deployment model

The demo uses Docker Compose to run:

- backend API
- Celery worker + beat
- Redis
- PostgreSQL
- EHR data service (FHIR-backed)
- frontend + nginx

All configuration is driven by `.env` / environment variables, and the knowledge base is mounted read-only into the runtime.

## Evaluation

Some performance numbers, background on data, future work.

<daata>

A limitation of the system is the rigor of the evaluation process. The data used was fully synthetic, though of relative high quality. All data originated from Synthea, a well regarded tool [A] that was also used to train MedGemma [B]. Some records were intentionally modified to trigger audit failures. It can bring about some interesting edge cases, but it is by no means complete. Getting access to real patient records along with audit results for evaluation would be a high priority for any future work.

## Future Objectives

We have a framework that connects various data sources and tools and that can be easily expanded to monitor/audit more areas of care with minimal marginal cost/effort. We have identified ICU handoff as our second area as handoff between departments is a large source of error, and mistakes can very quickly lead to patient harm. Real-time monitoring can help immensely in this area as the speed at which the issue is detected has an extremely high impact on the patient outcome.

- Research how to present FHIR data in a format that maximizes AI agent performance.
- Expand audit types (e.g., ICU handoff) by adding new prompt templates and guideline KB content.
- Report validation: MedArmor currently assumes the clinical report text is correct; future work could validate imaging interpretations when appropriate.

## Citations

[1] Mabotuwana, T., Hall, C. S., Tieder, J., & Gunn, M. L. (2018). Improving quality of follow-up imaging recommendations in radiology. AMIA Annual Symposium Proceedings, 2017, 1196–1204. https://pmc.ncbi.nlm.nih.gov/articles/PMC5977608/

[2] Reece, Jeanette C., et al. “Delayed or Failure to Follow-Up Abnormal Breast Cancer Screening Mammograms in Primary Care: A Systematic Review.” BMC Cancer, vol. 21, 7 Apr. 2021, article 373, https://pmc.ncbi.nlm.nih.gov/articles/PMC8028768

[3] Humphrey, Kate E., et al. “Frequency and Nature of Communication and Handoff Failures in Medical Malpractice Claims.” Journal of Patient Safety, vol. 18, no. 2, Mar. 2022, pp. 130–137, https://pubmed.ncbi.nlm.nih.gov/35188927

[A] Walonoski, Jason, et al. “Synthea: An Approach, Method, and Software Mechanism for Generating Synthetic Patients and the Synthetic Electronic Health Care Record.” Journal of the American Medical Informatics Association, vol. 25, no. 3, Mar. 2018, pp. 230–238. https://pubmed.ncbi.nlm.nih.gov/29025144

[B] Sellergren, Andrew, et al. “MedGemma Technical Report.” arXiv, 1st version, 7 July 2025. https://arxiv.org/html/2507.05201v1

[C] Lim, Jennifer Irene, et al. “Artificial Intelligence Detection of Diabetic Retinopathy: Subgroup Comparison of the EyeArt System with Ophthalmologists’ Dilated Examinations.” Ophthalmology Science, vol. 3, no. 1, 30 Sept. 2022, article 100228. https://pmc.ncbi.nlm.nih.gov/articles/PMC9636573/
