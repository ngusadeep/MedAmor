"""Audit engine: Uses LangGraph orchestrator for structured medical audits."""

from datetime import datetime, timezone
from uuid import UUID

from app.schemas.audit_report import (
    AuditReportCreate,
    EvidenceItem,
    FindingItem,
    OrchestratorAuditReport,
    OrchestratorEvidenceItem,
)
from app.services.audit_orchestrator import run_audit_orchestrator


def run_audit(
    job_id: UUID,
    patient_id: str,
    export_type: str | None = None,
    audit_type: str | None = None,
) -> AuditReportCreate:
    """
    Run one audit using LangGraph orchestrator: fetch EHR → retrieve guidelines → generate report.
    """
    audit_type = audit_type or "general"

    # Run the orchestrator
    orchestrator_result = run_audit_orchestrator(patient_id, audit_type)

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

    # Map status
    status = "NO_FINDINGS" if compliant else "FINDING_PRESENT"

    # Create findings from gaps
    findings = []
    corrective_actions = []

    for i, gap in enumerate(gaps):
        findings.append(
            FindingItem(
                category="Compliance Gap",
                description=gap,
                urgency="medium" if "critical" in gap.lower() else "low",
            )
        )
        corrective_actions.append(f"Address: {gap}")

    # Convert orchestrator evidence to our format
    evidence = []
    for item in evidence_items:
        if isinstance(item, dict):
            evidence.append(
                EvidenceItem(
                    kb_source=item.get("guideline", ""),
                    ehr_snippet=item.get("violation", ""),
                )
            )

    # Create executive summary
    if compliant:
        executive_summary = "Patient care appears compliant with clinical guidelines."
        risk_level = "low"
    else:
        gap_count = len(gaps)
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
