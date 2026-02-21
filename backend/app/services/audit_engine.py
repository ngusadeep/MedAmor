"""Audit engine: Uses LangGraph orchestrator for structured medical audits."""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
from uuid import UUID

from app.core.config import settings
from app.schemas.audit_report import (
    AuditReportCreate,
    EvidenceItem,
    FindingItem,
)
from app.services.audit_orchestrator import run_audit_orchestrator


def _apply_sensitivity_filter(
    findings: list[FindingItem],
    evidence: list[EvidenceItem],
    sensitivity: float,
) -> tuple[list[FindingItem], list[EvidenceItem]]:
    """
    Filter findings/evidence by confidence threshold derived from sensitivity.
    threshold = 1.0 - sensitivity: low sensitivity -> high threshold -> fewer items.
    """
    threshold = 1.0 - max(0.0, min(1.0, sensitivity))
    filtered_findings = [
        f
        for f in findings
        if (f.confidence or 0.5) >= threshold or (f.harm_severity or 0.5) >= threshold
    ]
    filtered_evidence = [
        e
        for e in evidence
        if (e.confidence or 0.5) >= threshold or (e.harm_severity or 0.5) >= threshold
    ]
    return filtered_findings, filtered_evidence


def run_audit(
    job_id: UUID,
    patient_id: str,
    export_type: str | None = None,
    audit_type: str | None = None,
    sensitivity: float | None = None,
    model: str | None = None,
    extraction_mode: str | None = None,
) -> AuditReportCreate:
    """
    Run one audit using LangGraph orchestrator: fetch EHR → retrieve guidelines → generate report.
    """
    audit_type = audit_type or "general"
    sens = sensitivity if sensitivity is not None else settings.audit_sensitivity

    logger.info(
        "run_audit job_id=%s patient_id=%s audit_type=%s export_type=%s sensitivity=%s model=%s extraction_mode=%s",
        job_id,
        patient_id,
        audit_type,
        export_type,
        sens,
        model,
        extraction_mode,
    )

    # Run the orchestrator with sensitivity and optional per-job overrides
    orchestrator_result = run_audit_orchestrator(
        patient_id,
        audit_type,
        sensitivity=sens,
        model=model,
        extraction_mode=extraction_mode,
    )

    # Parse the orchestrator report
    report_data = orchestrator_result.get("report", {})
    if isinstance(report_data, str):
        try:
            import json

            report_data = json.loads(report_data)
        except:
            report_data = {
                "compliant": False,
                "gaps": ["Failed to parse report"],
                "evidence": [],
            }

    # Convert orchestrator format to our schema format
    compliant = report_data.get("compliant", False)
    gaps = report_data.get("gaps", [])
    evidence_items = report_data.get("evidence", [])

    # Build evidence and findings; align by index for score propagation
    evidence = []
    for item in evidence_items:
        if isinstance(item, dict):
            evidence.append(
                EvidenceItem(
                    kb_source=item.get("guideline", ""),
                    ehr_snippet=item.get("violation", ""),
                    confidence=item.get("confidence"),
                    harm_severity=item.get("harm_severity"),
                )
            )

    findings = []
    corrective_actions = []
    for i, gap in enumerate(gaps):
        ev = evidence[i] if i < len(evidence) else None
        findings.append(
            FindingItem(
                category="Compliance Gap",
                description=gap,
                urgency="medium" if "critical" in gap.lower() else "low",
                confidence=ev.confidence if ev else None,
                harm_severity=ev.harm_severity if ev else None,
            )
        )
        corrective_actions.append(f"Address: {gap}")

    # Apply sensitivity filter
    findings, evidence = _apply_sensitivity_filter(findings, evidence, sens)
    # Sync corrective_actions with filtered findings
    corrective_actions = [f"Address: {f.description}" for f in findings]

    # Map status (NO_FINDINGS if compliant or all findings filtered out)
    status = "NO_FINDINGS" if compliant or len(findings) == 0 else "FINDING_PRESENT"

    # Create executive summary (use filtered findings count)
    if compliant or len(findings) == 0:
        executive_summary = "Patient care appears compliant with clinical guidelines."
        risk_level = "low"
    else:
        gap_count = len(findings)
        executive_summary = f"Audit identified {gap_count} potential compliance gap{'s' if gap_count != 1 else ''} requiring attention."
        risk_level = "high" if gap_count > 2 else "medium"

    return AuditReportCreate(
        job_id=job_id,
        patient_id=patient_id,
        status=status,
        risk_level=risk_level,
        executive_summary=executive_summary,
        findings=findings,
        evidence=evidence,
        corrective_actions=corrective_actions,
        next_audit_date=None,  # Could be calculated based on audit type
    )
