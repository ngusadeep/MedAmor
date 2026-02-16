"""Tests for AuditPromptBuilder."""

from aiorchestrator.guidelines.store import GuidelineChunk
from aiorchestrator.prompting.audit_prompt_builder import AuditPromptBuilder


def test_audit_prompt_builder_includes_timeline_and_guideline_ids() -> None:
    builder = AuditPromptBuilder()
    timeline = "2024-01-01: Patient admitted. HbA1c 7.2%."
    chunks = [
        GuidelineChunk(
            chunk_id="dm:protocol:0",
            audit_type="diabetes_management",
            text="HbA1c target <7%",
            source_file="protocol.md",
        ),
    ]
    prompt = builder.build(
        audit_type="diabetes_management",
        patient_timeline=timeline,
        guideline_chunks=chunks,
    )
    assert "diabetes_management" in prompt or "Diabetes" in prompt
    assert timeline in prompt
    assert "dm:protocol:0" in prompt
    assert "severity" in prompt.lower() or "findings" in prompt.lower()
