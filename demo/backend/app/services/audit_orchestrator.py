"""LangGraph StateGraph for medical audit orchestration - similar to aiorchestrator."""

from __future__ import annotations

import json
from typing import Annotated, TypedDict
from uuid import UUID

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import audit_ai, rag
from app.services.ehr_mock import get_patient_bundle


class EvidenceItem(BaseModel):
    guideline: str
    violation: str


class AuditReport(BaseModel):
    compliant: bool
    gaps: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class AuditState(TypedDict):
    """State schema for the audit graph."""
    patient_id: str
    audit_type: str
    ehr_data: str | None
    context: Annotated[list[str], lambda x, y: x + y]  # guideline chunks from RAG
    report: str


AUDIT_PROMPTS = {
    "breast_cancer_screening": """You are an expert Medical Auditor specializing in breast cancer screening. Audit the Patient History against the provided Clinical Guidelines.

## Patient History
{patient_summary}

## Clinical Guidelines (Breast Cancer Screening)
{guidelines}

## Instructions
1. Determine if the patient data is compliant with breast cancer screening guidelines.
2. Identify any gaps (missing screenings, inadequate follow-up, documentation issues).
3. For each gap, cite the specific guideline and the violation.

Return a JSON object with exactly these keys:
- compliant: boolean (true if compliant, false if gaps found)
- gaps: array of strings describing care gaps
- evidence: array of objects with "guideline" and "violation" keys
""",

    "hypertension_compliance": """You are an expert Medical Auditor specializing in hypertension management. Audit the Patient History against the provided Clinical Guidelines.

## Patient History
{patient_summary}

## Clinical Guidelines (Hypertension)
{guidelines}

## Instructions
1. Determine if the patient data is compliant with hypertension management guidelines.
2. Identify any gaps (uncontrolled BP, missing medications, inadequate monitoring).
3. For each gap, cite the specific guideline and the violation.

Return a JSON object with exactly these keys:
- compliant: boolean (true if compliant, false if gaps found)
- gaps: array of strings describing care gaps
- evidence: array of objects with "guideline" and "violation" keys
""",

    "diabetes_management": """You are an expert Medical Auditor specializing in diabetes care. Audit the Patient History against the provided Clinical Guidelines.

## Patient History
{patient_summary}

## Clinical Guidelines (Diabetes Management)
{guidelines}

## Instructions
1. Determine if the patient data is compliant with diabetes management guidelines.
2. Identify any gaps (poor glycemic control, missing screenings, inadequate monitoring).
3. For each gap, cite the specific guideline and the violation.

Return a JSON object with exactly these keys:
- compliant: boolean (true if compliant, false if gaps found)
- gaps: array of strings describing care gaps
- evidence: array of objects with "guideline" and "violation" keys
""",

    "general": """You are an expert Medical Auditor. Audit the Patient History against the provided Clinical Guidelines.

## Patient History
{patient_summary}

## Clinical Guidelines
{guidelines}

## Instructions
1. Determine if the patient data is compliant with clinical guidelines.
2. Identify any gaps in care, documentation, or follow-up.
3. For each gap, cite the specific guideline and the violation.

Return a JSON object with exactly these keys:
- compliant: boolean (true if compliant, false if gaps found)
- gaps: array of strings describing care gaps
- evidence: array of objects with "guideline" and "violation" keys
"""
}


def fetch_ehr_data(state: AuditState) -> dict:
    """Fetch patient EHR data from our EHR service."""
    patient_id = state["patient_id"]
    bundle = get_patient_bundle(patient_id, "full")
    ehr_text = bundle.ehr_text if bundle else ""

    return {"ehr_data": ehr_text}


def retrieve_guidelines(state: AuditState) -> dict:
    """Retrieve relevant clinical guidelines using RAG."""
    audit_type = state["audit_type"]
    ehr_data = state["ehr_data"] or ""

    # Build RAG query based on audit type
    query_map = {
        "breast_cancer_screening": "breast cancer screening mammography guidelines eligibility follow-up recall imaging documentation BI-RADS risk assessment",
        "hypertension_compliance": "hypertension treatment guidelines blood pressure targets lifestyle modifications medication therapy monitoring follow-up",
        "diabetes_management": "diabetes management glycemic control HbA1c targets screening complications medication insulin monitoring",
        "cardiology_compliance": "cardiology cardiovascular disease prevention risk assessment cholesterol lipids hypertension diabetes lifestyle",
        "general": "clinical audit imaging handoff continuity documentation follow-up quality care standards"
    }

    query = query_map.get(audit_type, query_map["general"])

    # Add patient context to query for better retrieval
    if ehr_data:
        # Extract key medical terms from EHR for better retrieval
        medical_terms = []
        if "hypertension" in ehr_data.lower() or "blood pressure" in ehr_data.lower():
            medical_terms.append("hypertension")
        if "diabetes" in ehr_data.lower():
            medical_terms.append("diabetes")
        if "breast" in ehr_data.lower() and ("cancer" in ehr_data.lower() or "mammogram" in ehr_data.lower()):
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
    ehr_data = state["ehr_data"] or ""
    context = state["context"]

    # Get the appropriate prompt
    prompt_template = AUDIT_PROMPTS.get(audit_type, AUDIT_PROMPTS["general"])

    # Format the prompt
    guidelines_text = "\n\n".join(context) if context else "No relevant guidelines found."
    patient_summary = ehr_data[:10000]  # Limit EHR text length

    full_prompt = prompt_template.format(
        patient_summary=patient_summary,
        guidelines=guidelines_text
    )

    # Use the configured AI provider
    provider = (settings.audit_ai_provider or "medgemma").strip().lower()

    if provider == "gemini" and settings.google_api_key:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model or "gemini-2.0-flash-exp",
                google_api_key=settings.google_api_key,
                temperature=0.2,
                max_tokens=1024
            )
            response = llm.invoke(full_prompt)
            raw_output = response.content
        except Exception:
            raw_output = '{"compliant": false, "gaps": ["AI analysis failed"], "evidence": []}'

    elif provider == "openai" and settings.openai_api_key:
        try:
            llm = ChatOpenAI(
                model=settings.openai_audit_model or "gpt-4",
                api_key=settings.openai_api_key,
                temperature=0.2,
                max_tokens=1024
            )
            response = llm.invoke(full_prompt)
            raw_output = response.content
        except Exception:
            raw_output = '{"compliant": false, "gaps": ["AI analysis failed"], "evidence": []}'

    else:
        # Fallback to existing audit_ai service
        ai_result = audit_ai.run_audit_ai(
            prompt=full_prompt,
            ehr_excerpt=ehr_data[:10000],
            kb_context=guidelines_text[:5000]
        )

        # Convert existing format to new structured format
        compliant = ai_result.get("status") == "NO_FINDINGS"
        gaps = []
        evidence = []

        if not compliant:
            findings = ai_result.get("findings", [])
            for finding in findings:
                if isinstance(finding, dict):
                    desc = finding.get("description", "")
                    if desc:
                        gaps.append(desc)

                    category = finding.get("category", "")
                    if category and desc:
                        evidence.append(EvidenceItem(
                            guideline=f"Category: {category}",
                            violation=desc
                        ))

        raw_output = AuditReport(
            compliant=compliant,
            gaps=gaps,
            evidence=evidence
        ).model_dump_json()

    return {"report": raw_output}


def build_audit_graph():
    """Build the LangGraph StateGraph for audit orchestration."""
    workflow = StateGraph(AuditState)

    # Add nodes
    workflow.add_node("fetch_ehr_data", fetch_ehr_data)
    workflow.add_node("retrieve_guidelines", retrieve_guidelines)
    workflow.add_node("generate_audit_report", generate_audit_report)

    # Add edges
    workflow.add_edge(START, "fetch_ehr_data")
    workflow.add_edge("fetch_ehr_data", "retrieve_guidelines")
    workflow.add_edge("retrieve_guidelines", "generate_audit_report")
    workflow.add_edge("generate_audit_report", END)

    return workflow.compile()


def run_audit_orchestrator(patient_id: str, audit_type: str = "general") -> dict:
    """
    Run the complete audit orchestration workflow.

    Args:
        patient_id: Patient identifier
        audit_type: Type of audit (breast_cancer_screening, hypertension_compliance, etc.)

    Returns:
        dict: Structured audit result with status, report, and sources
    """
    graph = build_audit_graph()

    result = graph.invoke({
        "patient_id": patient_id,
        "audit_type": audit_type,
        "ehr_data": None,
        "context": [],
        "report": ""
    })

    # Parse the report
    report_data = result.get("report", "{}")
    try:
        parsed_report = json.loads(report_data)
        # Ensure it has the expected structure
        if not isinstance(parsed_report, dict):
            parsed_report = {"compliant": False, "gaps": ["Invalid report format"], "evidence": []}
    except json.JSONDecodeError:
        parsed_report = {"compliant": False, "gaps": ["Failed to parse AI response"], "evidence": []}

    return {
        "status": "success",
        "patient_id": patient_id,
        "audit_type": audit_type,
        "report": parsed_report,
        "sources": result.get("context", []),
    }