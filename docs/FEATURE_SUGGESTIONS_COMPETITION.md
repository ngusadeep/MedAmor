# MedAudit — Feature Suggestions for MedGemma Impact Challenge

> Competition: https://www.kaggle.com/competitions/med-gemma-impact-challenge
> Deadline: ~3 days remaining
> Generated: 2026-02-22

---

## Current State

MedAudit is a breast cancer screening compliance audit tool with:

- **MedGemma** (text-only) via HF Inference API and Vertex AI
- **LangGraph** orchestration pipeline (4-node: fetch EHR → extract summary → retrieve guidelines → generate audit)
- **RAG** over clinical guidelines (ChromaDB + LangChain)
- **2-pass extraction** with configurable sensitivity tuning
- **Human-in-the-loop** annotations on AI-generated findings
- **Celery** async processing with scheduled daily audits
- **Multi-provider** support (MedGemma, Gemini, OpenAI)
- **~1,039 patient** EHR text records

### Key Gaps for the Competition

| Gap | Affected Criteria |
|-----|-------------------|
| No multimodal/image analysis | Effective use of HAI-DEF (20%) |
| Only 1 HAI-DEF model used (MedGemma text) | Effective use of HAI-DEF (20%) |
| No model performance benchmarking | Product Feasibility (20%) |
| Limited explainability visualization | Execution & Communication (30%) |
| Single audit type (breast cancer only) | Impact Potential (15%) |
| No patient-facing features | Problem Domain (15%) |

---

## Competition Scoring Breakdown

| Criteria | Weight | Description |
|----------|--------|-------------|
| Effective use of HAI-DEF models | 20% | Models used to fullest potential; other solutions less effective |
| Problem domain | 15% | Importance of problem, unmet need, user journey |
| Impact potential | 15% | Clear articulation of real or anticipated impact |
| Product feasibility | 20% | Technical docs, model performance analysis, deployment, practical use |
| Execution and communication | 30% | Video demo quality, write-up clarity, code quality, cohesive narrative |

---

## Feature 1: Mammography/CXR Image Analysis with MedGemma Multimodal

**Priority: CRITICAL**
**Effort: High**
**Criteria: Effective use of HAI-DEF (20%) + Product Feasibility (20%)**

### Problem

MedAudit audits breast cancer screening but only analyzes *text reports about images* — not the images themselves. A text-only audit tool doesn't uniquely need MedGemma; any LLM can do text analysis. Adding multimodal makes MedGemma *irreplaceable*.

### What to Build

- Upload mammography/CXR images alongside the EHR text for a patient
- **MedGemma 4B Multimodal** generates a structured radiology interpretation:
  - BI-RADS assessment category
  - Findings (masses, calcifications, architectural distortion)
  - Laterality and location
  - Breast density classification
- The audit pipeline **cross-references** the AI image interpretation against the radiologist's text report in the EHR
- Flag discrepancies (e.g., "AI detects suspicious calcification in left breast; report mentions right breast only")
- Creates a **second-opinion verification** workflow

### Technical Approach

1. Add image upload endpoint (`POST /api/patients/{id}/images`)
2. Store images in a volume-mounted directory or object storage
3. Add a new LangGraph node `analyze_imaging` between `fetch_ehr_data` and `extract_ehr_summary`
4. Call MedGemma 4B Multimodal via Vertex AI with the image + structured prompt
5. Pass AI imaging interpretation into the audit prompt as additional context
6. Add discrepancy detection logic in the audit prompt template
7. Frontend: image upload component in job creation dialog, image viewer in report detail

### Model Details

- **MedGemma 4B Multimodal**: 81% of CXR reports judged clinically sufficient by board-certified radiologists
- **MedGemma 27B Multimodal**: Higher accuracy for complex cases
- Supports: chest X-rays, mammography, CT slices, MRI slices

### Why It Wins Points

The judges want "applications that use HAI-DEF models to their fullest potential, where other solutions would likely be less effective." This feature makes MedGemma the core differentiator, not just another LLM provider.

---

## Feature 2: Explainability Dashboard — Confidence Visualization & Evidence Mapping

**Priority: HIGH**
**Effort: Medium**
**Criteria: Execution & Communication (30%) + Product Feasibility (20%)**

### Problem

MedAudit already has confidence scores and harm severity per finding — but they're rendered as raw numbers in a JSON-like list. The 30% "Execution and Communication" criteria rewards polish and visual narrative. Judges watching a 3-minute demo need to *see* the AI reasoning instantly.

### What to Build

#### Confidence Heatmap
- Visual indicator per finding showing confidence and harm severity as color-coded bars
- Green (high confidence, low harm) → Yellow (medium) → Red (low confidence, high harm)
- Makes it immediately clear which findings need human review

#### Evidence Chain Visualization
- Interactive flow diagram: **EHR excerpt → Guideline match → Finding → Corrective action**
- Click a finding to see exactly which EHR text and which guideline section produced it
- Implemented as a simple Sankey or flow chart using a React charting library

#### Interactive Sensitivity Slider
- Real-time slider on the report detail page
- As the reviewer adjusts sensitivity, findings appear/disappear based on their confidence/harm scores
- The data is already computed — this just re-filters the existing `findings` array client-side
- Demonstrates the sensitivity tuning feature powerfully in the demo video

#### Audit Quality Metrics Over Time
- Track AI vs. human agreement rate from annotation data
- Chart: "Of N findings annotated by clinicians, X% were confirmed, Y% were overridden"
- Shows the system improves over time with human feedback

### Technical Approach

1. Frontend-only for sensitivity slider (re-filter existing findings JSON)
2. Add a small charting library (e.g., Recharts, already common with shadcn)
3. Evidence chain: map `findings[i]` → `evidence[i]` relationships into a visual component
4. Aggregate annotation data into a new `/api/audit-reports/quality-metrics` endpoint

---

## Feature 3: Evaluation & Benchmarking Module

**Priority: HIGH**
**Effort: Medium**
**Criteria: Product Feasibility (20%) + Execution (30%)**

### Problem

The judges explicitly want "model's performance analysis." Without quantitative evidence, claims about MedGemma's effectiveness are unsubstantiated.

### What to Build

#### Benchmark Suite
- A script/endpoint that runs MedGemma against a curated set of patient EHRs with **ground truth labels** (manually annotated: expected findings, expected status, expected risk level)
- Compute: precision, recall, F1 for finding detection
- Compute: accuracy of BI-RADS categorization
- Compute: sensitivity/specificity at different threshold settings

#### Provider Comparison
- Run the same patient set through MedGemma, Gemini, and OpenAI
- Side-by-side table: latency, cost, accuracy, finding count, false positive rate
- Demonstrates MedGemma's advantage (privacy, cost, offline capability)

#### Annotation Agreement Rate
- When clinicians annotate AI findings as correct/incorrect, compute:
  - Cohen's kappa (inter-rater reliability)
  - Per-category accuracy (e.g., "BI-RADS follow-up gaps detected correctly 92% of the time")
- Track improvement over time as the system is used

#### Output
- JSON/CSV export of benchmark results
- Auto-generated performance summary table for the competition write-up
- Charts for the video demo

### Technical Approach

1. Create `scripts/benchmark.py` with ground truth JSON file
2. Add `POST /api/benchmark/run` endpoint (Chief Doctor only)
3. Store results in a `benchmark_runs` table
4. Frontend: benchmark results page with comparison charts
5. Create 20-30 ground truth cases from existing EHR data with manual labels

---

## Feature 4: MedASR — Clinical Voice Dictation for Audit Notes

**Priority: MEDIUM-HIGH**
**Effort: Medium**
**Criteria: Effective use of HAI-DEF (20%) + Problem Domain (15%)**

### Problem

Clinicians reviewing audit reports must type annotations — a friction point in real clinical workflows. MedASR is Google's newest HAI-DEF model (December 2025); using it signals full awareness of the HAI-DEF ecosystem.

### What to Build

- **Voice dictation button** on the report annotation form
- Clinician speaks their review notes → MedASR transcribes with medical terminology accuracy
- Auto-categorization: parse dictated notes into structured fields (agree/disagree, severity override, additional context)
- Works offline — MedASR is an open-weight model

### Technical Approach

1. Add MedASR as a backend service (lightweight, ~500MB model)
2. `POST /api/transcribe` endpoint: accepts audio blob, returns text
3. Frontend: record button using `MediaRecorder` API, send audio to backend
4. Optional: stream audio chunks for real-time transcription display
5. Post-transcription: use MedGemma to structure the free-text into annotation fields

### Model Details

- **MedASR**: Pre-trained on 5,000 hours of clinical audio
- Fine-tunable for specific vocabularies (e.g., breast cancer terminology)
- English only

### Why It Wins Points

Most competitors won't use MedASR. Using 3+ HAI-DEF models (MedGemma text, MedGemma multimodal, MedASR) demonstrates depth that a single-model demo cannot.

---

## Feature 5: Patient Communication Generator

**Priority: MEDIUM**
**Effort: Low-Medium**
**Criteria: Problem Domain (15%) + Impact Potential (15%)**

### Problem

Audits identify compliance gaps (e.g., overdue mammogram), but the workflow stops at the clinician. The patient — the actual person affected — is never notified through the system.

### What to Build

- After an audit identifies a gap, auto-generate a **patient-friendly notification letter** using MedGemma
- Configurable reading level: 5th grade, 8th grade, clinical
- Include: what screening is due, why it matters, how to schedule, personalized risk context
- Preview and edit before "sending" (human-in-the-loop)
- Multi-language support via MedGemma's multilingual capabilities

### Technical Approach

1. Add `POST /api/audit-reports/{id}/generate-letter` endpoint
2. Prompt MedGemma with the finding, corrective action, and reading level target
3. Return structured letter: greeting, explanation, action items, contact info
4. Frontend: letter preview modal on report detail page with reading level selector
5. Export as PDF

### Why It Wins Points

Shifts the narrative from "tool for auditors" → "tool that improves patient outcomes." Judges value "who the user is and their improved journey given your solution."

---

## Feature 6: Multi-Specialty Audit Expansion

**Priority: MEDIUM**
**Effort: Low**
**Criteria: Impact Potential (15%) + Problem Domain (15%)**

### Problem

MedAudit only audits breast cancer screening. Expanding to 2-3 more audit types demonstrates the platform is generalizable — a *platform*, not a one-trick demo.

### Suggested Audit Types

| Audit Type | Guidelines | Common Gaps |
|------------|-----------|-------------|
| **Diabetes Management** | ADA Standards of Care | HbA1c monitoring, foot exams, retinopathy screening, nephropathy screening |
| **Cardiovascular Risk** | ACC/AHA Guidelines | Statin therapy compliance, BP monitoring, lipid panel intervals |
| **Preventive Screening** | USPSTF Recommendations | Colonoscopy, cervical cancer screening, lung cancer LDCT |

### Technical Approach

1. Add 2-3 new guideline markdown files to `docs/Medical_KB/`
2. Add new entries in `AUDIT_PROMPTS` and `EXTRACTION_PROMPTS` dictionaries
3. Add specialty selector dropdown in the job creation dialog
4. RAG auto-indexes new guidelines on startup (already supported)
5. The rest of the pipeline works as-is — `audit_type` field already exists on jobs

### Why It Wins Points

Low effort, high narrative impact. "MedAudit supports 4 clinical specialties" sounds dramatically different from "MedAudit does breast cancer screening."

---

## Feature 7: MedSigLIP — Similar Case Retrieval

**Priority: MEDIUM**
**Effort: Medium**
**Criteria: Effective use of HAI-DEF (20%) + Impact Potential (15%)**

### Problem

When an audit flags a finding, clinicians lack institutional context: "Has this happened before? What was the outcome?"

### What to Build

- When an audit flags a finding, use **MedSigLIP** to search for similar historical cases
- "This BI-RADS 4 patient had a 6-month follow-up gap → here are 3 similar patients and their outcomes"
- **Similar Cases** panel on the report detail page
- For imaging-enabled patients: find visually similar mammograms for case-based reasoning

### Technical Approach

1. Generate MedSigLIP embeddings for all patient audit reports (text or images)
2. Store embeddings in ChromaDB (separate collection from guideline KB)
3. On report generation, compute embedding for new case and find k-nearest neighbors
4. `GET /api/audit-reports/{id}/similar-cases` endpoint
5. Frontend: collapsible "Similar Cases" section on report detail page

---

## Feature 8: Agentic Workflow — Multi-Step Clinical Reasoning

**Priority: LOWER**
**Effort: High**
**Criteria: Effective use of HAI-DEF (20%) + Product Feasibility (20%)**

### Problem

The current LangGraph pipeline is a linear 4-node chain. Agentic workflows with conditional branching demonstrate sophisticated AI orchestration.

### What to Build

#### Conditional Routing
- If EHR extraction finds imaging references → branch to MedGemma Multimodal analysis
- If medication references → branch to drug interaction check
- If multiple specialties relevant → fan out to parallel audit pipelines

#### Self-Verification Loop
- After generating the audit report, a second MedGemma call verifies each finding against evidence
- "Does finding X actually follow from evidence Y?"
- Flag low-confidence self-assessments for human review

#### Escalation Logic
- If AI confidence < threshold → auto-flag for senior clinician review
- If findings conflict with each other → generate a "conflicting evidence" summary
- Never render a verdict when uncertain — defer to human judgment

#### Agent Trace Visualization
- Show which LangGraph nodes fired, what decisions were made, and the data at each step
- Interactive timeline in the UI

### Technical Approach

1. Refactor `build_audit_graph()` to use conditional edges (`add_conditional_edges`)
2. Add verification node after `generate_audit_report`
3. Add escalation node with confidence-based routing
4. Store agent trace metadata in the job record
5. Frontend: collapsible "AI Reasoning Path" on report detail

---

## 3-Day Sprint Recommendation

Given ~3 days remaining, prioritize features that maximize scoring across the most criteria:

### Day 1: MedGemma Multimodal (Feature 1)
- Even a proof-of-concept with sample mammography images
- Addresses the 20% HAI-DEF criteria directly
- Makes the demo video visually compelling

### Day 2: Explainability Dashboard (Feature 2) + Multi-Specialty (Feature 6)
- Confidence visualization, evidence chains, interactive sensitivity slider
- Add 1-2 new audit types (copy guideline pattern from breast cancer)
- Addresses the 30% Execution criteria through demo polish

### Day 3: Benchmarking (Feature 3) + Write-up + Video
- Run provider comparison, generate performance tables
- Write the 3-page report using benchmark data
- Record the 3-minute demo video showcasing all features

### Stretch Goals (if time permits)
- MedASR voice dictation (Feature 4)
- Patient letter generator (Feature 5)

---

## HAI-DEF Model Coverage

| Model | Current Usage | Proposed Usage |
|-------|--------------|----------------|
| **MedGemma (text)** | Primary audit AI | Keep as-is |
| **MedGemma (multimodal)** | Not used | Feature 1: Mammography analysis |
| **MedASR** | Not used | Feature 4: Voice dictation |
| **MedSigLIP** | Not used | Feature 7: Similar case retrieval |
| **Path Foundation** | Not used | Future: histopathology audit |
| **TxGemma** | Not used | Future: drug interaction checks |
| **HeAR** | Not used | Not applicable to this domain |

Using 3-4 HAI-DEF models (MedGemma text + multimodal + MedASR + MedSigLIP) would demonstrate exceptional breadth and set MedAudit apart from single-model submissions.
