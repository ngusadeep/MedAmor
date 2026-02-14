"""Tests for bundle_to_timeline_text."""
import pytest

from aiorchestrator.fhir_reader_adapter import bundle_to_timeline_text


def test_bundle_to_timeline_text_returns_string() -> None:
    bundle = {
        "resourceType": "Bundle",
        "type": "document",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "p1", "birthDate": "1990-01-01"}},
        ],
    }
    result = bundle_to_timeline_text(bundle)
    assert isinstance(result, str)
    assert len(result) >= 0


def test_bundle_to_timeline_text_empty_bundle() -> None:
    bundle = {"resourceType": "Bundle", "type": "document", "entry": []}
    result = bundle_to_timeline_text(bundle)
    assert isinstance(result, str)
