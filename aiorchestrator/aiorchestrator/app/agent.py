"""LangGraph StateGraph for medical audit orchestration."""

from __future__ import annotations

import json
import operator
from typing import Annotated, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .fhir import format_patient_summary
from .vector_store import get_vector_store


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
    fhir_data: dict | None
    context: Annotated[list[str], operator.add]  # guideline chunks from RAG
    report: str


AUDIT_PROMPT = """You are an expert Medical Auditor. Audit the Patient History against the provided Clinical Guidelines.

## Patient History
{patient_summary}

## Clinical Guidelines (for {audit_type})
{guidelines}

## Instructions
1. Determine if the patient data is compliant with the guidelines.
2. Identify any gaps (missing care, unmet targets, deviations).
3. For each gap, cite the specific guideline and the violation.

Output ONLY valid JSON with this exact structure (no markdown, no extra text):
{{"compliant": boolean, "gaps": ["string"], "evidence": [{{"guideline": "string", "violation": "string"}}]}}"""


def _get_vector_store():
    return get_vector_store()


# Dummy FHIR bundle for development – replace with real API call when ready
DUMMY_FHIR_BUNDLE = {
    "resourceType": "Bundle",
    "type": "document",
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "example",
                "name": [{"given": ["John"], "family": "Doe"}],
                "birthDate": "1965-03-15",
                "gender": "male",
            }
        },
        {
            "resource": {
                "resourceType": "Observation",
                "id": "obs-1",
                "code": {"coding": [{"display": "Blood pressure", "code": "85354-9"}]},
                "valueQuantity": {"value": 142, "unit": "mmHg"},
                "effectiveDateTime": "2024-01-10",
            }
        },
        {
            "resource": {
                "resourceType": "Observation",
                "id": "obs-2",
                "code": {"coding": [{"display": "Diastolic blood pressure", "code": "8462-4"}]},
                "valueQuantity": {"value": 88, "unit": "mmHg"},
                "effectiveDateTime": "2024-01-10",
            }
        },
        {
            "resource": {
                "resourceType": "Condition",
                "id": "cond-1",
                "code": {"coding": [{"display": "Essential hypertension", "code": "38341003"}]},
                "onsetDateTime": "2023-06-01",
            }
        },
    ],
}


def fetch_fhir(state: AuditState) -> dict:
    """Fetch patient data (dummy – returns sample bundle; swap for real FHIR API later)."""
    patient_id = state["patient_id"]
    # Dummy: return sample bundle keyed by patient_id for testing variation
    bundle = {**DUMMY_FHIR_BUNDLE}
    if bundle.get("entry"):
        bundle["entry"][0]["resource"]["id"] = patient_id
    return {"fhir_data": bundle}


def retrieve_docs(state: AuditState) -> dict:
    """Vector search on ChromaDB using Google Embeddings for clinical guidelines."""
    audit_type = state["audit_type"]
    patient_summary = ""

    if state.get("fhir_data"):
        patient_summary = format_patient_summary(state["fhir_data"])

    query = f"{audit_type}: {patient_summary}" if patient_summary else audit_type
    vs = _get_vector_store()
    docs = vs.similarity_search(query, k=5)
    context = [d.page_content for d in docs]
    return {"context": context}


def generate_report(state: AuditState) -> dict:
    """Call Gemini to audit patient data against retrieved guidelines (structured output)."""
    import os

    patient_summary = format_patient_summary(state.get("fhir_data") or {"entry": []})
    context_chunks = state.get("context") or []
    guidelines = "\n\n".join(context_chunks)
    audit_type = state.get("audit_type", "general")

    llm = ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp"),
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        temperature=0,
    )

    structured_llm = llm.with_structured_output(AuditReport)

    prompt = AUDIT_PROMPT.format(
        patient_summary=patient_summary,
        audit_type=audit_type,
        guidelines=guidelines or "No guidelines available.",
    )

    try:
        result: AuditReport = structured_llm.invoke(prompt)
        report = json.dumps(
            {
                "compliant": result.compliant,
                "gaps": result.gaps,
                "evidence": [{"guideline": e.guideline, "violation": e.violation} for e in result.evidence],
            },
            indent=2,
        )
    except Exception as e:
        report = json.dumps(
            {
                "compliant": False,
                "gaps": ["LLM invocation failed"],
                "evidence": [{"guideline": "error", "violation": str(e)}],
            },
            indent=2,
        )

    return {"report": report}


def build_audit_graph():
    """Build and compile the audit StateGraph."""
    builder = StateGraph(AuditState)

    builder.add_node("fetch_fhir", fetch_fhir)
    builder.add_node("retrieve_docs", retrieve_docs)
    builder.add_node("generate_report", generate_report)

    builder.add_edge(START, "fetch_fhir")
    builder.add_edge("fetch_fhir", "retrieve_docs")
    builder.add_edge("retrieve_docs", "generate_report")
    builder.add_edge("generate_report", END)

    return builder.compile()
