# Feature Enhancement: 2-Pass Extraction, Confidence/Harm Scores, Sensitivity + UI Controls

## Overview

This document specifies enhancements to the MedAudit AI pipeline and tracks what is **already implemented** vs what remains.

1. **Configurable 2-pass extraction** — optional EHR extraction pass before the audit verdict
2. **Confidence & harm scores** — each finding/evidence item gets confidence + harm severity
3. **Sensitivity tuning** — a threshold parameter that filters findings by confidence/harm
4. **UI controls** — make key knobs adjustable from the frontend UI (new)

All changes must preserve the current 1-pass behaviour as the default.

## Status (current repo)

**Implemented (backend):**
- **2-pass extraction (configurable)**: `AUDIT_EXTRACTION_MODE=one_pass|gemini_extract|medgemma_extract` (default `one_pass`)
- **Confidence + harm severity fields**: propagated through orchestrator → stored report JSON → API schema
- **Sensitivity tuning**: global default `AUDIT_SENSITIVITY` + per-job override `sensitivity` (filtered server-side)
- **Manual DB migration script**: `backend/migrations/add_job_sensitivity.sql`

**Not yet implemented (frontend UI):**
- **Sensitivity control** in the “Create Job” dialog (single + batch)
- (Optional / recommended) **Extraction mode control** exposed in UI (see approaches below)

---

## 1. Configurable 2-Pass Extraction

### Problem

The current pipeline feeds raw, truncated EHR text (hard cap at 10,000 chars) directly into the audit prompt. For long patient records, critical clinical events beyond the cutoff are silently lost. There is no AI-driven extraction step to identify and surface relevant facts before auditing.

### Proposed Extraction Modes

| Mode                | Pass 1 (Extraction)        | Pass 2 (Audit Verdict)  | External Calls  |
|---------------------|----------------------------|-------------------------|-----------------|
| `ONE_PASS`          | *none* (current behaviour) | configured provider     | depends on provider |
| `GEMINI_EXTRACT`    | Gemini                     | configured provider     | yes (Google API) |
| `MEDGEMMA_EXTRACT`  | MedGemma (HF endpoint)     | configured provider     | HF only (can be local) |

`ONE_PASS` and `MEDGEMMA_EXTRACT` allow fully offline operation (assuming a local HF endpoint).

### Status: Implemented (backend)

Backend implementation matches the intent above:
- A new LangGraph node `extract_ehr_summary` runs between EHR fetch and guideline retrieval.
- In `one_pass` mode it’s a no-op.
- In extraction modes, Pass 1 uses a larger EHR window (~30k chars) to generate a distilled summary used in Pass 2.

### Files to Change

#### `backend/app/core/config.py` (Settings)

**What:** Add new env var `AUDIT_EXTRACTION_MODE`.

```python
# Add to the Settings class (after audit_ai_provider, ~line 85):
audit_extraction_mode: Literal["one_pass", "gemini_extract", "medgemma_extract"] = "one_pass"
```

**Why:** This is the single toggle. Default `"one_pass"` means zero behaviour change for existing deployments.

#### `.env.example`

**What:** Document the new variable.

```env
# After AUDIT_AI_PROVIDER line (~line 47):
# Extraction mode: one_pass | gemini_extract | medgemma_extract
# gemini_extract requires GOOGLE_API_KEY; medgemma_extract requires HF_TOKEN + HF_MEDGEMMA_ENDPOINT
AUDIT_EXTRACTION_MODE=one_pass
# Sensitivity: 0.0 (only critical) to 1.0 (surface everything). Default 0.5.
AUDIT_SENSITIVITY=0.5
```

#### `backend/app/services/audit_orchestrator.py` (LangGraph graph)

This is the primary change. The 3-node linear graph becomes a 4-node graph with a conditional first extraction node.

**What — new state field** (~line 27, `AuditState`):

```python
class AuditState(TypedDict):
    patient_id: str
    audit_type: str
    extraction_mode: str              # NEW — "one_pass" | "gemini_extract" | "medgemma_extract"
    ehr_data: str | None              # raw EHR text (unchanged)
    extracted_summary: str | None     # NEW — structured extraction from Pass 1
    context: Annotated[list[str], operator.add]
    report: str
```

**What — new extraction prompt** (add after `AUDIT_PROMPTS` dict, ~line 110):

Add an `EXTRACTION_PROMPT` template that asks the AI to produce a structured JSON summary of the EHR: relevant diagnoses, screening dates, labs, medications, follow-ups, risk factors. This prompt should be audit-type-aware (the extraction query for breast cancer screening differs from hypertension).

**What — new node function `extract_ehr_summary`** (add after `fetch_ehr_data`, ~line 119):

```python
def extract_ehr_summary(state: AuditState) -> dict:
    """Pass 1: Use AI to extract clinically relevant facts from raw EHR."""
    mode = state.get("extraction_mode", "one_pass")
    if mode == "one_pass":
        return {"extracted_summary": None}

    ehr_data = state.get("ehr_data") or ""
    audit_type = state.get("audit_type", "general")
    prompt_template = EXTRACTION_PROMPTS.get(audit_type, EXTRACTION_PROMPTS["general"])
    raw = audit_ai.run_extraction(
        prompt=prompt_template,
        ehr_text=ehr_data[:30000],
        mode=mode,
    )
    return {"extracted_summary": raw or None}
```

Key detail: the extraction pass gets a **much larger context window** (up to 30,000 chars of raw EHR vs the current 10,000) because its only job is to distill, not reason about guidelines.

**Implementation note (current repo):**

- Extraction is invoked via `backend/app/services/audit_ai.py` `run_extraction()`.
- Provider-specific raw helpers are implemented as `_run_gemini_raw()` and `_run_medgemma_raw()`.
- MedGemma raw call is implemented in `backend/app/services/medgemma.py` as `run_medgemma_raw()`.

**What — modify `generate_audit_report`** (~line 160):

```python
def generate_audit_report(state: AuditState) -> dict:
    # If extraction was performed, use the extracted summary instead of raw EHR
    if state.get("extracted_summary"):
        patient_summary = state["extracted_summary"][:15000]
    else:
        patient_summary = (state["ehr_data"] or "")[:10000]

    # ... rest unchanged
```

**What — modify `build_audit_graph`** (~line 212):

```python
def build_audit_graph():
    workflow = StateGraph(AuditState)

    workflow.add_node("fetch_ehr_data", fetch_ehr_data)
    workflow.add_node("extract_ehr_summary", extract_ehr_summary)   # NEW
    workflow.add_node("retrieve_guidelines", retrieve_guidelines)
    workflow.add_node("generate_audit_report", generate_audit_report)

    workflow.add_edge(START, "fetch_ehr_data")
    workflow.add_edge("fetch_ehr_data", "extract_ehr_summary")      # NEW
    workflow.add_edge("extract_ehr_summary", "retrieve_guidelines")  # NEW
    workflow.add_edge("retrieve_guidelines", "generate_audit_report")
    workflow.add_edge("generate_audit_report", END)

    return workflow.compile()
```

The new node sits between fetch and retrieve. In `ONE_PASS` mode it's a no-op (returns `None`). No conditional routing needed; the node just short-circuits.

**What — modify `run_audit_orchestrator`** (~line 230):

```python
def run_audit_orchestrator(patient_id: str, audit_type: str = "general") -> dict:
    graph = build_audit_graph()
    result = graph.invoke({
        "patient_id": patient_id,
        "audit_type": audit_type,
        "extraction_mode": settings.audit_extraction_mode,  # NEW — from config
        "ehr_data": None,
        "extracted_summary": None,  # NEW
        "context": [],
        "report": "",
    })
    # ... rest unchanged
```

#### `backend/app/services/audit_ai.py`

**What:** Add an extraction-mode dispatch function (~after `run_audit_ai`, line 133):

```python
def run_extraction(
    prompt: str,
    ehr_text: str,
    mode: str,
) -> str:
    """Run Pass 1 extraction. Returns raw text (not structured audit report)."""
    if mode == "gemini_extract":
        return _run_gemini_raw(prompt, ehr_text)
    return _run_medgemma_raw(prompt, ehr_text)
```

Add `_run_gemini_raw` and `_run_medgemma_raw` variants that return the raw model output string (no JSON parsing), reusing existing API call logic.

#### Notes

- **Extraction mode** is currently **global config-driven** (via `.env`) and does not require per-request API changes.
- **EHR and RAG services** are unchanged by extraction mode: `ehr_mock.py`, `ehr_client.py`, `rag.py`.

---

## 2. Confidence & Harm Scores

### Problem

Every finding today has equal weight. The PM wants each finding to carry a **confidence score** (how sure the AI is) and a **harm severity** (clinical impact), so reviewers can prioritise and sensitivity can be tuned.

### Files to Change

#### `backend/app/services/audit_orchestrator.py` — Prompt Templates

**What:** Update every prompt in `AUDIT_PROMPTS` (~lines 37–110) to ask the model for two additional fields per finding:

```
For each gap, also provide:
- confidence: float 0.0–1.0 (how confident you are this is a real gap)
- harm_severity: float 0.0–1.0 (potential patient harm if this gap is unaddressed)
```

And update the expected JSON schema in the prompt:

```
- evidence: array of objects with "guideline", "violation", "confidence", "harm_severity" keys
```

#### `backend/app/services/audit_orchestrator.py` — `EvidenceItem` model

**What:** Extend the Pydantic model (~line 16):

```python
class EvidenceItem(BaseModel):
    guideline: str
    violation: str
    confidence: float = 0.5       # NEW
    harm_severity: float = 0.5    # NEW
```

#### `backend/app/services/audit_orchestrator.py` — `generate_audit_report` function

**What:** Parse the new fields when building evidence items (~line 199):

```python
evidence.append(
    EvidenceItem(
        guideline=f"Category: {category}",
        violation=desc,
        confidence=finding.get("confidence", 0.5),          # NEW
        harm_severity=finding.get("harm_severity", 0.5),    # NEW
    )
)
```

#### `backend/app/schemas/audit_report.py` — `FindingItem`

**What:** Add score fields (~line 9):

```python
class FindingItem(BaseModel):
    category: str
    description: str
    responsible_doctor: str | None = None
    urgency: str | None = None
    confidence: float | None = None       # NEW
    harm_severity: float | None = None    # NEW
```

#### `backend/app/schemas/audit_report.py` — `EvidenceItem`

**What:** Add score fields (~line 18):

```python
class EvidenceItem(BaseModel):
    kb_source: str | None = None
    ehr_snippet: str | None = None
    image_ref: str | None = None
    confidence: float | None = None       # NEW
    harm_severity: float | None = None    # NEW
```

#### `backend/app/services/audit_engine.py` — score propagation

**What:** When converting orchestrator output to `AuditReportCreate` (~lines 56–75), pass through the new scores:

```python
findings.append(
    FindingItem(
        category="Compliance Gap",
        description=gap,
        urgency="medium" if "critical" in gap.lower() else "low",
        confidence=...,        # NEW — from orchestrator evidence
        harm_severity=...,     # NEW — from orchestrator evidence
    )
)
```

#### `backend/app/models/audit_report.py` — DB column

**No schema migration required.** The `findings` and `evidence` columns are already `JSONB`, so the new fields are stored automatically when the Pydantic models serialize.

---

## 3. Sensitivity Tuning

### Problem

The PM wants a **sensitivity dial**: low sensitivity = only high-confidence, high-harm findings surface; high sensitivity = more findings, including speculative ones. This lets new customers start conservative and gradually increase.

### Design

A single `sensitivity` parameter (float 0.0–1.0, default `0.5`) acts as a **post-filter threshold** on findings:

```
included = confidence >= (1.0 - sensitivity) OR harm_severity >= (1.0 - sensitivity)
```

| Sensitivity | Min confidence/harm to include | Behaviour                  |
|-------------|-------------------------------|----------------------------|
| 0.2 (low)   | 0.8                           | Only near-certain, high-harm findings |
| 0.5 (default)| 0.5                          | Balanced                   |
| 0.9 (high)  | 0.1                           | Almost everything surfaces |

### Files to Change

#### `backend/app/core/config.py`

**What:** Add default sensitivity (~after `audit_extraction_mode`):

```python
audit_sensitivity: float = 0.5  # 0.0 (lowest) to 1.0 (highest)
```

#### `.env.example`

```env
# Sensitivity: 0.0 (only critical) to 1.0 (surface everything). Default 0.5.
AUDIT_SENSITIVITY=0.5
```

#### `backend/app/schemas/job.py` — `JobCreate`

**What:** Allow per-job sensitivity override (~line 18):

```python
class JobCreate(BaseModel):
    patient_id: str
    audit_type: str | None = None
    export_type: str | None = None
    triggered_by: str | None = None
    sensitivity: float | None = None   # NEW — override global default
```

#### `backend/app/models/job.py` — Job model

**What:** Store per-job sensitivity (~after `export_type`, line 49):

```python
sensitivity: Mapped[float | None] = mapped_column(nullable=True)
```

**Note:** This repo does not use Alembic migrations; DB tables are created via `Base.metadata.create_all()` (`backend/app/core/database.py`).  
For existing databases, run the manual SQL migration: `backend/migrations/add_job_sensitivity.sql`.

#### `backend/app/services/audit_engine.py` — post-filter

**What:** After building the findings list, filter by sensitivity (~after line 64):

```python
def _apply_sensitivity_filter(
    findings: list[FindingItem],
    evidence: list[EvidenceItem],
    sensitivity: float,
) -> tuple[list[FindingItem], list[EvidenceItem]]:
    """Filter findings/evidence by confidence threshold derived from sensitivity."""
    threshold = 1.0 - sensitivity
    filtered_findings = [
        f for f in findings
        if (f.confidence or 0.5) >= threshold or (f.harm_severity or 0.5) >= threshold
    ]
    filtered_evidence = [
        e for e in evidence
        if (e.confidence or 0.5) >= threshold or (e.harm_severity or 0.5) >= threshold
    ]
    return filtered_findings, filtered_evidence
```

Call this at the end of `run_audit()` before constructing `AuditReportCreate`, using `sensitivity` passed from the job or falling back to `settings.audit_sensitivity`.

#### `backend/app/services/audit_engine.py` — function signature

**What:** Accept `sensitivity` parameter:

```python
def run_audit(
    job_id: UUID,
    patient_id: str,
    export_type: str | None = None,
    audit_type: str | None = None,
    sensitivity: float | None = None,  # NEW
) -> AuditReportCreate:
```

#### `backend/app/worker/tasks.py` — pass sensitivity through

**What:** Read `job.sensitivity` and pass to `run_audit()` (~line 53):

```python
report_create = run_audit(
    job.id,
    job.patient_id,
    job.export_type,
    getattr(job, "audit_type", None),
    sensitivity=job.sensitivity,  # NEW
)
```

#### `backend/app/routers/jobs.py` — accept sensitivity in request

**What:** Pass `body.sensitivity` when creating the job (~line 47):

```python
job = _create_one_job(
    db,
    body.patient_id,
    audit_type=body.audit_type,
    export_type=body.export_type,
    triggered_by=body.triggered_by,
    sensitivity=body.sensitivity,  # NEW
)
```

And update `_create_one_job` to accept and store `sensitivity`.

---

## 4. UI Controls (New Work)

You want these features to be changeable from the UI. The backend already supports per-job `sensitivity`; extraction mode is currently **global via env** only.

### 4.1 Add sensitivity control to Create Job (recommended; minimal backend work)

**Goal:** Let the user choose `sensitivity` (0.0–1.0) when creating single or batch jobs.

**Frontend files to change:**
- `frontend/src/features/audits/components/create-job-dialog.tsx`
  - Add a slider or radio presets (e.g. Low=0.2, Medium=0.5, High=0.8)
  - Pass `sensitivity` into `createJob()` and `createJobsBatch()` payloads
- `frontend/src/lib/jobs-api.ts`
  - Extend `JobCreate` and `JobCreateBatch` interfaces with `sensitivity?: number`
- (Optional) `frontend/src/features/audits/components/jobs-columns.tsx`
  - Add a column for `sensitivity` to make job settings visible

### 4.2 Extraction mode in UI (two approaches)

Right now, extraction mode is set via `.env` (`AUDIT_EXTRACTION_MODE`) and cannot be changed from the UI without further backend work.

#### Option A (recommended for demo): per-job extraction mode override

**Goal:** Add an `extraction_mode` dropdown in Create Job and store it on the job.

**Backend changes needed (not implemented yet):**
- Add `extraction_mode` to:
  - `backend/app/schemas/job.py` (`JobCreate`, `JobCreateBatch`, `JobResponse`)
  - `backend/app/models/job.py` (new nullable column on `jobs`)
  - `backend/app/routers/jobs.py` (persist it on job create)
  - `backend/app/worker/tasks.py` (pass through to `run_audit()`)
  - `backend/app/services/audit_engine.py` / `backend/app/services/audit_orchestrator.py` (prefer job override over global default)
- Add a manual SQL migration for existing DBs (similar to `add_job_sensitivity.sql`)

**Frontend changes needed:**
- `frontend/src/features/audits/components/create-job-dialog.tsx`: dropdown values:
  - `one_pass`
  - `medgemma_extract` (offline-friendly)
  - `gemini_extract` (external call)
- `frontend/src/lib/jobs-api.ts`: add `extraction_mode?: string`

#### Option B: global “Audit Settings” page/drawer (admin)

**Goal:** Add a UI panel that changes global defaults for extraction mode + sensitivity.

This requires a backend settings API and persistence (DB/Redis). The existing `ConfigDrawer` (`frontend/src/components/config-drawer.tsx`) is currently **theme/layout only**; it could be extended once backend support exists.

---

## Implementation Order

| Priority | Task                                         | Estimated Effort |
|----------|----------------------------------------------|-----------------|
| 1        | (DONE) Add `AUDIT_EXTRACTION_MODE` to config + .env | — |
| 2        | (DONE) Add `extract_ehr_summary` node + extraction prompts to orchestrator | — |
| 3        | (DONE) Add `run_extraction` + raw-output helpers to `audit_ai.py` | — |
| 4        | (DONE) Wire extraction node into LangGraph graph    | — |
| 5        | (DONE) Add confidence/harm fields to schemas + models | — |
| 6        | (DONE) Update `AUDIT_PROMPTS` to request scores     | — |
| 7        | (DONE) Parse + propagate scores in orchestrator → engine | — |
| 8        | (DONE) Add sensitivity config + per-job field + DB migration | — |
| 9        | (DONE) Implement `_apply_sensitivity_filter` in audit_engine | — |
| 10       | (DONE) Wire sensitivity through router → task → engine | — |
| 11       | (DONE) Update `.env.example` with all new vars      | — |
| 12       | Frontend: add sensitivity control to Create Job (single + batch) | Small |
| 13       | (Optional) Frontend: show sensitivity in jobs table | Small |
| 14       | (Optional) Add per-job extraction mode override end-to-end | Medium |

---

## Files Changed Summary

| File | Changes |
|------|---------|
| `backend/app/core/config.py` | Add `audit_extraction_mode`, `audit_sensitivity` |
| `backend/app/services/audit_orchestrator.py` | New `AuditState` fields, new node, extraction prompts, updated graph, score parsing |
| `backend/app/services/audit_ai.py` | Add `run_extraction()`, raw-output helper variants |
| `backend/app/services/medgemma.py` | Add `run_medgemma_raw()` for extraction |
| `backend/app/services/audit_engine.py` | Accept `sensitivity`, add `_apply_sensitivity_filter`, propagate scores |
| `backend/app/schemas/audit_report.py` | Add `confidence`, `harm_severity` to `FindingItem` and `EvidenceItem` |
| `backend/app/schemas/job.py` | Add `sensitivity` to `JobCreate` + `JobCreateBatch` + `JobResponse` |
| `backend/app/models/job.py` | Add `sensitivity` column |
| `backend/app/routers/jobs.py` | Pass `sensitivity` through job creation |
| `backend/app/worker/tasks.py` | Pass `job.sensitivity` to `run_audit()` |
| `.env.example` | Document `AUDIT_EXTRACTION_MODE`, `AUDIT_SENSITIVITY` |
| `backend/migrations/add_job_sensitivity.sql` | Manual DB migration for existing databases |

No changes to: `ehr_mock.py`, `ehr_client.py`, `rag.py`, `patient_enrichment.py`, `celery_app.py`, DB model `audit_report.py` (JSONB handles new fields).
