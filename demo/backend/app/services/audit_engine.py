"""Audit engine: EHR + RAG context → MedGemma → structured report (findings, evidence, actions).
Focused on Breast Cancer Screening Audit."""

from datetime import datetime, timezone
from uuid import UUID

from app.schemas.audit_report import AuditReportCreate, EvidenceItem, FindingItem
from app.services import audit_ai, rag
from app.services.ehr_mock import get_patient_bundle

AUDIT_SYSTEM_PROMPT = """You are a clinical audit assistant for breast cancer screening compliance. Do NOT diagnose. Based on the provided EHR excerpt and knowledge base context (screening guidelines, mammography, follow-up), produce a structured audit report in JSON with exactly 
these keys: status (NO_FINDINGS or FINDING_PRESENT), risk_level (low/medium/high), executive_summary (string), findings (list of {category, description, responsible_doctor?, urgency?}), evidence (list of {kb_source?, ehr_snippet?}), corrective_actions (list of strings). Cite evidence only from the given context."""

# RAG query tuned for breast cancer screening guidelines retrieval
RAG_QUERY_BREAST_CANCER_SCREENING = (
    "breast cancer screening mammography guidelines eligibility follow-up "
    "recall imaging documentation BI-RADS risk assessment"
)


def run_audit(
    job_id: UUID,
    patient_id: str,
    export_type: str | None = None,
    audit_type: str | None = None,
) -> AuditReportCreate:
    """
    Run one audit: load EHR, retrieve RAG context (Breast Cancer Screening guidelines), call MedGemma, return report.
    """
    export_type = export_type or "full"
    bundle = get_patient_bundle(patient_id, export_type)
    ehr_text = bundle.ehr_text if bundle else ""

    query = (
        RAG_QUERY_BREAST_CANCER_SCREENING
        if (audit_type or "").strip().lower() == "breast_cancer_screening"
        else "clinical audit imaging handoff continuity documentation follow-up"
    )
    chunks = rag.retrieve(query, k=6)
    kb_context = "\n\n".join(c["text"] for c in chunks) if chunks else ""

    prompt = AUDIT_SYSTEM_PROMPT
    out = audit_ai.run_audit_ai(
        prompt=prompt,
        ehr_excerpt=ehr_text[:14000],
        kb_context=kb_context[:8000] if kb_context else None,
    )

    status = out.get("status", "NO_FINDINGS")
    risk_level = out.get("risk_level")
    executive_summary = out.get("executive_summary")
    findings_raw = out.get("findings") or []
    evidence_raw = out.get("evidence") or []
    corrective_actions = out.get("corrective_actions") or []
    next_audit = out.get("next_audit_date")

    findings = [
        FindingItem(
            category=f.get("category", ""),
            description=f.get("description", ""),
            responsible_doctor=f.get("responsible_doctor"),
            urgency=f.get("urgency"),
        )
        for f in findings_raw
        if isinstance(f, dict)
    ]
    evidence = [
        EvidenceItem(
            kb_source=e.get("kb_source"),
            ehr_snippet=e.get("ehr_snippet"),
            image_ref=e.get("image_ref"),
        )
        for e in evidence_raw
        if isinstance(e, dict)
    ]
    next_dt = None
    if next_audit:
        try:
            if isinstance(next_audit, str):
                next_dt = datetime.fromisoformat(next_audit.replace("Z", "+00:00"))
            elif isinstance(next_audit, datetime):
                next_dt = next_audit
        except Exception:
            pass
    if next_dt and next_dt.tzinfo is None:
        next_dt = next_dt.replace(tzinfo=timezone.utc)

    return AuditReportCreate(
        job_id=job_id,
        patient_id=patient_id,
        status=status,
        risk_level=risk_level,
        executive_summary=executive_summary,
        findings=findings,
        evidence=evidence,
        corrective_actions=corrective_actions,
        next_audit_date=next_dt,
    )
