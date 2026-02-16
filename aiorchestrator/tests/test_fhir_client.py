"""Tests for MockFHIRClient."""

import json
import tempfile
from pathlib import Path

import pytest

from aiorchestrator.fhir_client.mock import MockFHIRClient


def test_mock_fhir_client_returns_well_formed_bundle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sample_dir = Path(tmp)
        bundle = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [{"resource": {"resourceType": "Patient", "id": "test"}}],
        }
        (sample_dir / "patient_test.json").write_text(
            json.dumps(bundle), encoding="utf-8"
        )
        client = MockFHIRClient(sample_dir=str(sample_dir))
        result = client.get_patient_bundle("test")
        assert result["resourceType"] == "Bundle"
        assert len(result["entry"]) == 1
        assert result["entry"][0]["resource"]["resourceType"] == "Patient"


def test_mock_fhir_client_unknown_id_raises_or_uses_default() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sample_dir = Path(tmp)
        (sample_dir / "patient_default.json").write_text(
            json.dumps({"resourceType": "Bundle", "type": "document", "entry": []}),
            encoding="utf-8",
        )
        client = MockFHIRClient(sample_dir=str(sample_dir))
        result = client.get_patient_bundle("unknown")
        assert result["resourceType"] == "Bundle"


def test_mock_fhir_client_empty_patient_id_raises() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client = MockFHIRClient(sample_dir=str(tmp))
        with pytest.raises(ValueError, match="patient_id"):
            client.get_patient_bundle("")
