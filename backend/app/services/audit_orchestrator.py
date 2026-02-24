"""LangGraph StateGraph for medical audit orchestration - similar to aiorchestrator."""

from __future__ import annotations

import json
import logging
from datetime import date

logger = logging.getLogger(__name__)
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import audit_ai, rag
from app.services.ehr_mock import get_patient_bundle


class EvidenceItem(BaseModel):
    guideline: str
    violation: str
    confidence: float = 0.5
    harm_severity: float = 0.5


class AuditReport(BaseModel):
    compliant: bool
    gaps: list[str] = Field(default_factory=list)
    close_calls: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class AuditState(TypedDict):
    """State schema for the audit graph."""

    patient_id: str
    audit_type: str
    extraction_mode: str
    sensitivity: float
    model: str | None
    ehr_data: str | None
    extracted_summary: str | None
    context: Annotated[list[str], operator.add]
    report: str


AUDIT_PROMPTS = {
    "breast_cancer_screening": """You are an expert Medical Auditor specializing in breast cancer screening compliance.

Your job is to compare a patient's clinical history against breast cancer screening guidelines and flag every gap.

TODAY'S DATE: {today_date}

## Patient History
{patient_summary}

## Clinical Guidelines (Breast Cancer Screening)
{guidelines}

{sensitivity_directive}

## Audit Checklist — evaluate each item
1. **Screening interval & Rolling Deadlines**: Identify the date of the MOST RECENT mammogram. Infer its BI-RADS category if not explicitly stated (e.g., "improving" but not fully normal = Category 2 or 3).
   - Add the guideline-required interval (e.g., 12 months for Category 2/Surveillance) to that most recent date to find the NEXT due date.
   - Compare the NEXT due date to TODAY ({today_date}). If the due date has passed, this is an ACTIVE GAP.

2. **BI-RADS follow-up — CRITICAL**: Look for any BI-RADS score in the imaging results. Apply these MANDATORY deadlines measured from the date of the imaging:
   - BI-RADS 3: repeat mammogram within 6 months
   - BI-RADS 4A (low suspicion): image-guided core biopsy within 2–4 weeks
   - BI-RADS 4B/4C/5: urgent biopsy within 1-2 weeks maximum
   If no biopsy or follow-up imaging is documented AND the deadline has passed relative to {today_date}, that is a gap.

3. **BI-RADS 6 / Known malignancy & Surveillance — CRITICAL**: If the patient has a biopsy-proven cancer diagnosis:
   a. Verify a cancer treatment plan is documented.
   b. Verify an oncology referral is documented.
   c. Verify a surveillance mammogram occurred 6–12 months after treatment completion.
   d. ONGOING SURVEILLANCE: Annual mammograms must continue every 12 months indefinitely. Calculate the months elapsed between the MOST RECENT mammogram and TODAY ({today_date}). If this gap exceeds 12 months, flag it as "Overdue annual surveillance".

## Rules
- **Evaluate current status only.** If an item is currently overdue as of {today_date}, it is a gap.
- **Close calls.** If a past action was completed late, record it in "close_calls" (e.g., "First surveillance mammogram done 12 months late"). This does not count as an active gap.
- Absence of evidence of a completed scan or biopsy IS an active gap.

Return ONLY a JSON object (no markdown fences, no explanation outside the JSON).
IMPORTANT: You MUST start your JSON with a "_thought_process" array. You must do the following math for every patient:
- "The most recent mammogram was on [Date]."
- "The results indicated [Status/Category], which requires a follow-up in [X months]."
- "Adding [X months] to [Date] makes the next scan due on [Due Date]."
- "Since today is {today_date}, this scan is [Overdue / Not Overdue]."

Your JSON must contain exactly these keys in this order:
- "_thought_process": array of strings (briefly summarizing the steps outlined above)
- "compliant": boolean (false only if there are active, unresolved gaps)
- "gaps": array of strings, each describing one currently outstanding care gap
- "close_calls": array of strings
- "evidence": array of objects: "guideline" (string), "violation" (string), "confidence" (float 0.0-1.0), "harm_severity" (float 0.0-1.0)
""",
    "general": """You are an expert Medical Auditor. Audit the Patient History against the provided Clinical Guidelines.

TODAY'S DATE: {today_date}

## Patient History
{patient_summary}

## Clinical Guidelines
{guidelines}

{sensitivity_directive}

## Instructions
1. Determine if the patient data is **currently** compliant with clinical guidelines as of today ({today_date}).
2. Identify any gaps in care, documentation, or follow-up that are **still outstanding and unresolved**.
3. If a required action was completed late (past its guideline deadline) but HAS been completed, do NOT list it as a gap — it is resolved. Record it as a close call instead.
4. For each gap, cite the specific guideline and the violation.
5. Absence of evidence of a completed action IS a gap.
6. For each gap, assign confidence (0.0-1.0) and harm_severity (0.0-1.0).

Return ONLY a JSON object (no markdown fences, no explanation outside the JSON) with exactly these keys:
- "compliant": boolean (false only if there are active, unresolved gaps)
- "gaps": array of strings describing currently outstanding care gaps
- "close_calls": array of strings describing actions that were completed but were late — include what was done and the approximate delay (e.g. "Follow-up imaging performed 3 months late")
- "evidence": array of objects with "guideline", "violation", "confidence" (0.0-1.0), "harm_severity" (0.0-1.0) keys
""",
}

EXTRACTION_PROMPTS = {
    "breast_cancer_screening": """You are a clinical data extraction specialist. Extract ALL information relevant to a breast cancer screening audit from this patient record.

You MUST extract every instance of the following, with dates wherever available:

1. **Cancer diagnoses**: Any mention of breast cancer, carcinoma, neoplasm, tumor, malignancy — include date of diagnosis, type, stage, grade.
2. **Mammograms / breast imaging**: Every mammogram, breast MRI, breast ultrasound — include date, result, BI-RADS score if present.
3. **Biopsies and pathology**: Any breast biopsy — date, type (core needle, surgical), result (benign, malignant, DCIS, etc.).
4. **Screening intervals**: Calculate the time gap (in months) between consecutive mammograms. Highlight if any gap exceeds 12 months for high-risk or 24 months for average-risk patients.
5. **Risk factors**: Family history of breast/ovarian cancer, BRCA status, prior breast findings, hormone therapy, age at menarche/menopause, radiation exposure.
6. **Treatment history**: Surgery (lumpectomy, mastectomy), radiation, chemotherapy, hormone therapy — with dates.
7. **Treatment history**: Surgery (lumpectomy, mastectomy), radiation, chemotherapy, hormone therapy — with dates. Note the approximate date treatment was completed or is ongoing.
8. **Follow-up and referrals**: Oncology referrals, recommended follow-up imaging, whether follow-ups were completed or are overdue.
9. **Post-treatment surveillance**: For patients with a known cancer diagnosis, list every mammogram or imaging study performed AFTER the cancer diagnosis date, with dates. Calculate the gap in months between the most recent post-diagnosis imaging and the end of the record.
10. **Most recent encounter date**: The date of the patient's last recorded visit.

If a data point is not found in the record, explicitly state "NOT FOUND IN RECORD" for that item. Do NOT omit missing items.

Return the extraction as structured plain text with clear section headers.""",
    "general": """Extract clinically relevant information for a medical audit from this patient record.

Focus on:
- All diagnoses with dates
- All screenings, imaging, and labs with dates and results
- Medications (current and historical)
- Procedures and surgeries with dates
- Follow-up recommendations and whether they were completed
- Most recent encounter date
- Any gaps where expected follow-up or screening is missing

If a data point is not found in the record, explicitly state "NOT FOUND IN RECORD".

Return the extraction as structured plain text with clear section headers.""",
}


def _sensitivity_directive(sensitivity: float) -> str:
    """Build a prompt directive that tells the model how aggressively to flag issues."""
    s = max(0.0, min(1.0, sensitivity))
    if s >= 0.7:
        return (
            "## Sensitivity: HIGH\n"
            "Flag ALL potential gaps, even minor, uncertain, or borderline ones. "
            "When in doubt, flag it. Absence of documentation for a recommended "
            "screening counts as a gap. Assign confidence honestly but do not "
            "suppress low-confidence findings — include them all."
        )
    if s >= 0.4:
        return (
            "## Sensitivity: MEDIUM\n"
            "Flag clear gaps and probable issues. Include items where evidence "
            "is missing but the screening or follow-up was likely expected. "
            "Skip only clearly insignificant or inapplicable items."
        )
    return (
        "## Sensitivity: LOW\n"
        "Flag only definitive, critical gaps with strong evidence. "
        "Omit speculative or minor issues."
    )


def fetch_ehr_data(state: AuditState) -> dict:
    """Fetch patient EHR data from our EHR service."""
    patient_id = state["patient_id"]
    bundle = get_patient_bundle(patient_id, "full")
    ehr_text = bundle.ehr_text if bundle else ""
    ehr_len = len(ehr_text)
    preview = (ehr_text[:500] + "...") if len(ehr_text) > 500 else ehr_text
    logger.info(
        "audit_ehr_fetched patient_id=%s ehr_length=%d preview=%s",
        patient_id,
        ehr_len,
        repr(preview[:200]),
    )
    return {"ehr_data": ehr_text}


def extract_ehr_summary(state: AuditState) -> dict:
    """Pass 1: Use AI to extract clinically relevant facts from raw EHR."""
    mode = state.get("extraction_mode", "one_pass")
    if mode == "one_pass":
        return {"extracted_summary": None}

    ehr_data = state.get("ehr_data") or ""
    audit_type = state.get("audit_type", "general")
    prompt_template = EXTRACTION_PROMPTS.get(audit_type, EXTRACTION_PROMPTS["general"])
    full_prompt = prompt_template  # no patient_record placeholder; ehr_text passed separately

    raw = audit_ai.run_extraction(
        prompt=full_prompt,
        ehr_text=ehr_data,
        mode=mode,
    )
    return {"extracted_summary": raw or None}


def retrieve_guidelines(state: AuditState) -> dict:
    """Retrieve relevant clinical guidelines — full file load or RAG, based on AUDIT_GUIDELINES_MODE."""
    guidelines_mode = getattr(settings, "audit_guidelines_mode", "rag")

    if guidelines_mode == "full":
        # Load entire KB from disk — no embeddings, no ChromaDB. Suitable when there is one guideline file.
        kb_docs = rag.load_kb_documents(settings.medical_kb_path_resolved)
        if kb_docs:
            combined = "\n\n---\n\n".join(content for content, _ in kb_docs)
            logger.info(
                "guidelines_mode=full loaded %d doc(s), total_len=%d",
                len(kb_docs),
                len(combined),
            )
            return {"context": [combined]}
        logger.warning("guidelines_mode=full: no documents found under %s", settings.medical_kb_path_resolved)
        return {"context": []}

    # --- RAG path (default) ---
    audit_type = state["audit_type"]
    ehr_data = state["ehr_data"] or ""

    query_map = {
        "breast_cancer_screening": "breast cancer screening mammography guidelines eligibility follow-up recall imaging documentation BI-RADS risk assessment",
        "hypertension_compliance": "hypertension treatment guidelines blood pressure targets lifestyle modifications medication therapy monitoring follow-up",
        "diabetes_management": "diabetes management glycemic control HbA1c targets screening complications medication insulin monitoring",
        "cardiology_compliance": "cardiology cardiovascular disease prevention risk assessment cholesterol lipids hypertension diabetes lifestyle",
        "general": "clinical audit imaging handoff continuity documentation follow-up quality care standards",
    }

    query = query_map.get(audit_type, query_map["general"])

    if ehr_data:
        medical_terms = []
        if "hypertension" in ehr_data.lower() or "blood pressure" in ehr_data.lower():
            medical_terms.append("hypertension")
        if "diabetes" in ehr_data.lower():
            medical_terms.append("diabetes")
        if "breast" in ehr_data.lower() and (
            "cancer" in ehr_data.lower() or "mammogram" in ehr_data.lower()
        ):
            medical_terms.append("breast cancer screening")
        if medical_terms:
            query = f"{' '.join(medical_terms)} {query}"

    chunks = rag.retrieve(query, k=5)
    context = [c["text"] for c in chunks] if chunks else []

    return {"context": context}


def generate_audit_report(state: AuditState) -> dict:
    """Generate structured audit report using AI."""
    patient_id = state["patient_id"]
    audit_type = state["audit_type"]
    sensitivity = state.get("sensitivity", 0.5)
    ehr_data = state.get("ehr_data") or ""

    patient_summary = state.get("extracted_summary") or ehr_data
    logger.info(
        "audit_ai_call patient_id=%s audit_type=%s patient_summary_len=%d sensitivity=%s",
        patient_id,
        audit_type,
        len(patient_summary),
        sensitivity,
    )
    context = state.get("context", [])

    prompt_template = AUDIT_PROMPTS.get(audit_type, AUDIT_PROMPTS["general"])

    guidelines_text = (
        "\n\n".join(context) if context else "No relevant guidelines found."
    )
    sens_directive = _sensitivity_directive(sensitivity)

    full_prompt = prompt_template.format(
        patient_summary=patient_summary,
        guidelines=guidelines_text,
        sensitivity_directive=sens_directive,
        today_date=date.today().isoformat(),
    )

    # full_prompt already contains patient data, guidelines, and sensitivity —
    # pass it as the sole prompt to avoid duplicating content.
    model_override = state.get("model")
    ai_result = audit_ai.run_audit_ai(prompt=full_prompt, model_override=model_override)

    compliant = ai_result.get("compliant", ai_result.get("status") == "NO_FINDINGS")
    gaps = list(ai_result.get("gaps", []))
    close_calls = list(ai_result.get("close_calls", []))
    evidence = []

    # Build evidence from "evidence" (model format) or "findings" (stub/legacy)
    ev_items = ai_result.get("evidence", []) or ai_result.get("findings", [])
    for item in ev_items:
        if not isinstance(item, dict):
            continue
        guideline = item.get("guideline", item.get("category", ""))
        violation = item.get("violation", item.get("description", ""))
        if guideline or violation:
            evidence.append(
                EvidenceItem(
                    guideline=guideline or "Unknown",
                    violation=violation or "",
                    confidence=float(item.get("confidence", 0.5)),
                    harm_severity=float(item.get("harm_severity", 0.5)),
                )
            )
    if not gaps and evidence:
        gaps = [e.violation for e in evidence if e.violation]

    raw_output = AuditReport(
        compliant=compliant, gaps=gaps, close_calls=close_calls, evidence=evidence
    ).model_dump_json()

    return {"report": raw_output}


def build_audit_graph():
    """Build the LangGraph StateGraph for audit orchestration."""
    workflow = StateGraph(AuditState)

    workflow.add_node("fetch_ehr_data", fetch_ehr_data)
    workflow.add_node("extract_ehr_summary", extract_ehr_summary)
    workflow.add_node("retrieve_guidelines", retrieve_guidelines)
    workflow.add_node("generate_audit_report", generate_audit_report)

    workflow.add_edge(START, "fetch_ehr_data")
    workflow.add_edge("fetch_ehr_data", "extract_ehr_summary")
    workflow.add_edge("extract_ehr_summary", "retrieve_guidelines")
    workflow.add_edge("retrieve_guidelines", "generate_audit_report")
    workflow.add_edge("generate_audit_report", END)

    return workflow.compile()


def run_audit_orchestrator(
    patient_id: str,
    audit_type: str = "general",
    sensitivity: float = 0.5,
    model: str | None = None,
    extraction_mode: str | None = None,
) -> dict:
    """
    Run the complete audit orchestration workflow.

    Args:
        patient_id: Patient identifier
        audit_type: Type of audit (breast_cancer_screening, general, etc.)
        sensitivity: 0.0 (only critical) to 1.0 (flag everything)
        model: Optional per-job override: medgemma_hf | medgemma_vertex | gemini | openai
        extraction_mode: Optional per-job override: one_pass | gemini_extract | medgemma_extract

    Returns:
        dict: Structured audit result with status, report, and sources
    """
    graph = build_audit_graph()

    extraction_mode_val = extraction_mode or getattr(
        settings, "audit_extraction_mode", "one_pass"
    )
    logger.info(
        "audit_orchestrator_start patient_id=%s audit_type=%s extraction_mode=%s sensitivity=%s model=%s",
        patient_id,
        audit_type,
        extraction_mode_val,
        sensitivity,
        model,
    )
    result = graph.invoke(
        {
            "patient_id": patient_id,
            "audit_type": audit_type,
            "extraction_mode": extraction_mode_val,
            "sensitivity": sensitivity,
            "model": model,
            "ehr_data": None,
            "extracted_summary": None,
            "context": [],
            "report": "",
        }
    )

    # Parse the report
    report_data = result.get("report", "{}")
    try:
        parsed_report = json.loads(report_data)
        # Ensure it has the expected structure
        if not isinstance(parsed_report, dict):
            parsed_report = {
                "compliant": False,
                "gaps": ["Invalid report format"],
                "evidence": [],
            }
    except json.JSONDecodeError:
        parsed_report = {
            "compliant": False,
            "gaps": ["Failed to parse AI response"],
            "evidence": [],
        }

    return {
        "status": "success",
        "patient_id": patient_id,
        "audit_type": audit_type,
        "report": parsed_report,
        "sources": result.get("context", []),
    }
