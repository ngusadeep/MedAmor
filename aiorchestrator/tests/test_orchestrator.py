"""End-to-end test for AuditOrchestrator with mocks."""

import json
import tempfile
from pathlib import Path

import pytest

from aiorchestrator.fhir_client.mock import MockFHIRClient
from aiorchestrator.fhir_reader_adapter import bundle_to_timeline_text
from aiorchestrator.guidelines.retriever import GuidelineRetriever
from aiorchestrator.guidelines.store import GuidelineStore
from aiorchestrator.prompting.audit_prompt_builder import AuditPromptBuilder
from aiorchestrator.llm.mock import MockLLMClient
from aiorchestrator.orchestrator.audit_orchestrator import AuditOrchestrator


@pytest.fixture
def sample_fhir_dir(tmp_path: Path) -> Path:
    bundle = {
        "resourceType": "Bundle",
        "type": "document",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "e2e",
                    "birthDate": "1985-05-01",
                }
            },
        ],
    }
    (tmp_path / "patient_e2e.json").write_text(json.dumps(bundle), encoding="utf-8")
    return tmp_path


@pytest.fixture
def guidelines_dir(tmp_path: Path) -> Path:
    (tmp_path / "hypertension").mkdir()
    (tmp_path / "hypertension" / "protocol.md").write_text(
        "## Purpose\nHypertension management.\n\n## Classification\nStage 1: 130-139/80-89.",
        encoding="utf-8",
    )
    return tmp_path


def test_orchestrator_run_audit_end_to_end(
    sample_fhir_dir: Path, guidelines_dir: Path
) -> None:
    fhir_client = MockFHIRClient(sample_dir=str(sample_fhir_dir))
    store = GuidelineStore(guidelines_dir=str(guidelines_dir))
    store.load()
    retriever = GuidelineRetriever(store=store, top_k=5)
    prompt_builder = AuditPromptBuilder()
    llm_client = MockLLMClient()
    orchestrator = AuditOrchestrator(
        fhir_client=fhir_client,
        timeline_converter=bundle_to_timeline_text,
        guideline_retriever=retriever,
        prompt_builder=prompt_builder,
        llm_client=llm_client,
    )
    result = orchestrator.run_audit(patient_id="e2e", audit_type="hypertension")
    assert result["patient_id"] == "e2e"
    assert result["audit_type"] == "hypertension"
    assert "prompt" in result
    assert "llm_output" in result
    assert "guideline_sources" in result
    assert "Mock audit report" in result["llm_output"]
