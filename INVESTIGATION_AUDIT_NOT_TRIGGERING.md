# Investigation: Audit Not Triggering on Cancer Patient

**Date:** 2026-02-21
**Symptom:** Patient has detected cancer with no screening in 12+ months. Gemini returns "No findings."
**Patient timeline:** ~25,000 characters

---

## Root Causes Found

### 1. CRITICAL — Prompt Triple-Stuffing (Patient Data + Guidelines Sent 3×)

This is the single biggest problem. The data is sent to Gemini **three times** in the same request.

**How it happens:**

In `audit_orchestrator.py` → `generate_audit_report`:

```python
full_prompt = prompt_template.format(
    patient_summary=patient_summary,   # ← data baked INTO the prompt string
    guidelines=guidelines_text          # ← guidelines baked INTO the prompt string
)

ai_result = audit_ai.run_audit_ai(
    prompt=full_prompt,                # ← already contains both
    ehr_excerpt=patient_summary,       # ← sent AGAIN
    kb_context=guidelines_text,        # ← sent AGAIN
)
```

Then in `audit_ai.py` → `_run_gemini`, `_build_prompt_parts` assembles:

```
## Knowledge base context          ← guidelines (copy 1)
{guidelines_text}

## Patient EHR excerpt             ← patient data (copy 1)
{patient_summary}

## Instruction                     ← the formatted prompt, which ALREADY contains:
  ## Patient History               ← patient data (copy 2)
  {patient_summary}
  ## Clinical Guidelines           ← guidelines (copy 2)
  {guidelines_text}
```

**Impact:** If the extracted summary from Pass 1 is ~4k chars and guidelines are ~5k chars, the final prompt is **~27k chars** instead of the expected ~9k. In one_pass mode with the full 25k EHR, the prompt balloons to **~75k+ chars**. Gemini gets confused by the repetition and either:
- Loses focus on the actual audit task buried in the noise
- Treats the duplicated sections as conflicting context
- Produces a vague or overly cautious (compliant) response

---

### 2. CRITICAL — Sensitivity Filter Silently Drops All Findings

Even if Gemini **does** detect gaps, the sensitivity filter in `audit_engine.py` can remove every single one:

```python
threshold = 1.0 - sensitivity   # 1.0 - 0.5 = 0.5

filtered_findings = [
    f for f in findings
    if (f.confidence or 0.5) >= threshold
    or (f.harm_severity or 0.5) >= threshold
]
```

Then:

```python
status = "NO_FINDINGS" if compliant or len(findings) == 0 else "FINDING_PRESENT"
```

If Gemini returns confidence/harm_severity values below 0.5 for its findings (which it commonly does for screening gaps vs. active harm), **every finding is filtered out** and the final status is `NO_FINDINGS` — even though the model said `compliant: false`.

**Current `.env` setting:** `AUDIT_SENSITIVITY=0.5` → threshold = 0.5 → anything below 0.5 confidence AND below 0.5 severity is dropped.

---

### 3. HIGH — Audit Type Mismatch (General vs. Cancer-Specific)

If the job is created with `audit_type=general` (the default), the system uses a generic prompt:

> "Determine if the patient data is compliant with clinical guidelines. Identify any gaps in care, documentation, or follow-up."

This prompt does **not** mention cancer, screening intervals, or follow-up protocols. The model has no directive to flag a 12-month screening gap specifically.

The `breast_cancer_screening` prompt **does** explicitly ask:

> "Identify any gaps (missing screenings, inadequate follow-up, documentation issues)."

**Also affects RAG retrieval:** The RAG query for `general` is:
`"clinical audit imaging handoff continuity documentation follow-up quality care standards"`
— nothing about cancer screening guidelines. The retrieved KB chunks may be irrelevant.

---

### 4. HIGH — Extraction Prompt Too Vague for General Audit Type

With `AUDIT_EXTRACTION_MODE=gemini_extract`, Pass 1 extracts a summary from the 25k EHR. The extraction prompt for `general` is:

> "Extract clinically relevant information for a general medical audit. Focus on: key diagnoses, medications, procedures, labs, imaging, follow-up recommendations, documentation of care."

This is too broad. For a 25k-char record, the model may summarize the most recent encounters or the most voluminous sections, **omitting** the cancer diagnosis date and the last screening date because they're just two lines buried in a long timeline.

The `max_output_tokens=2048` for extraction (~1,500 words) further constrains how much detail survives Pass 1.

---

### 5. MEDIUM — JSON Parsing Greedy Regex Risk

The parser uses:

```python
m = re.search(r"\{[\s\S]*\}", raw)
```

This is **greedy** — it matches from the **first** `{` to the **last** `}` in the entire response. If Gemini's response includes any explanatory text with braces before or after the JSON block, the regex captures garbage around the actual JSON, causing `json.loads` to fail. When parsing fails, the code falls back to `STUB_REPORT` with `status: NO_FINDINGS`.

---

### 6. LOW — Sensitivity Config Exists but Is Never Passed to the Model

`AUDIT_SENSITIVITY=0.5` is only used **post-hoc** to filter results. It is never injected into the prompt to tell the model *how aggressively* to flag issues. The model has no awareness of the desired sensitivity level and makes its own judgment about what constitutes a "gap."

---

## Data Flow Diagram (Current)

```
Patient EHR (25k chars)
       │
       ▼
┌─────────────────────┐
│ Pass 1: Extraction   │  gemini_extract, max_output_tokens=2048
│ (general prompt)     │  → vague extraction, may lose cancer dates
└──────────┬──────────┘
           │ ~2-4k char summary
           ▼
┌─────────────────────┐
│ RAG: Guidelines      │  query = generic keywords, may miss cancer guidelines
└──────────┬──────────┘
           │ ~5k guidelines (possibly irrelevant)
           ▼
┌─────────────────────┐
│ Pass 2: Audit        │  prompt.format(patient_summary, guidelines)
│                      │  THEN run_audit_ai(prompt, ehr_excerpt, kb_context)
│                      │  → TRIPLE-STUFFED prompt (~27k+ chars)
└──────────┬──────────┘
           │ Gemini response (JSON)
           ▼
┌─────────────────────┐
│ Parse JSON           │  greedy regex → may fail → STUB (NO_FINDINGS)
└──────────┬──────────┘
           │ compliant: false, gaps: [...], evidence: [...]
           ▼
┌─────────────────────┐
│ Sensitivity Filter   │  threshold=0.5, drops low-confidence items
│                      │  if ALL filtered → status = NO_FINDINGS
└──────────┬──────────┘
           │
           ▼
       NO_FINDINGS  ← even though model found gaps
```

---

## Recommendations (Priority Order)

### Fix 1: Stop Double/Triple-Sending Data

In `generate_audit_report`, either:
- **Option A:** Pass `full_prompt` to `run_audit_ai` with `ehr_excerpt=None, kb_context=None` (since the template already has both).
- **Option B:** Pass the raw prompt template (before `.format()`) and let `_build_prompt_parts` assemble everything once.

### Fix 2: Log and Surface Sensitivity Filtering

Before the filter, log what the model returned. If findings exist but are filtered, the status should reflect that (e.g. `FILTERED` or at minimum a log warning). Consider raising `AUDIT_SENSITIVITY` to 0.7–0.8 to lower the threshold and keep more findings.

### Fix 3: Use Cancer-Specific Audit Type

When creating jobs for known cancer patients, use `audit_type=breast_cancer_screening` (or the appropriate cancer type). This gives the model the right prompt, the right extraction focus, and the right RAG query.

### Fix 4: Make Extraction Prompts Condition-Aware

For two-pass mode, the extraction prompt should be guided by the audit type. The `general` extraction prompt should at minimum ask for: "screening dates and intervals, last follow-up dates, flagged conditions and their monitoring status."

### Fix 5: Use Non-Greedy JSON Regex

Change the regex to non-greedy or use a proper JSON extractor:
```python
# non-greedy: find the first complete JSON object
m = re.search(r"\{[\s\S]*?\}", raw)
```
Or better: look for ```json fenced blocks first, then fall back to regex.

### Fix 6: Inject Sensitivity into the Prompt

Tell the model the sensitivity level so it knows whether to flag borderline issues:
> "Sensitivity level: HIGH. Flag any potential gaps, even minor or uncertain ones."

---

## Quick Test Checklist

- [ ] Check terminal logs for `gemini PROMPT:` — is patient data appearing 2-3 times?
- [ ] Check logs for `gemini RESPONSE:` — did the model return `compliant: false` with gaps?
- [ ] Check logs for `gemini parse FAILED` — did JSON parsing fail?
- [ ] Check if findings exist pre-filter but are removed by sensitivity (no log for this currently)
- [ ] Verify the `audit_type` on the job row — is it `general` or `breast_cancer_screening`?
- [ ] Try running with `AUDIT_SENSITIVITY=0.9` to see if findings appear
