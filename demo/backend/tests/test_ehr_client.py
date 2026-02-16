"""Tests for EHR client (service URL)."""

from unittest.mock import patch

import httpx
import pytest

from app.schemas.ehr import EHRPatientBundle, EHRPatientSummary
from app.services.ehr_client import (
    get_patient_bundle_from_service,
    list_patients_from_service,
)


def test_list_patients_from_service_success():
    """list_patients_from_service returns parsed list from /patients."""
    response_data = [
        {"patient_id": "p1", "patient_name": "Alice", "export_types": ["full"]},
        {"patient_id": "p2", "patient_name": None, "export_types": ["full", "minimal"]},
    ]
    req = httpx.Request("GET", "http://ehr:8000/patients")

    def fake_get(url, **kwargs):
        assert "patients" in url and "/patients" in url
        return httpx.Response(200, json=response_data, request=req)

    with patch("app.services.ehr_client.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get = fake_get
        result = list_patients_from_service("http://ehr:8000")
        assert len(result) == 2
        assert result[0].patient_id == "p1"
        assert result[0].patient_name == "Alice"
        assert result[1].patient_id == "p2"
        assert result[1].patient_name is None


def test_get_patient_bundle_from_service_200():
    """get_patient_bundle_from_service returns bundle on 200."""
    response_data = {
        "patient_id": "p1",
        "export_type": "full",
        "ehr_text": "Timeline content here.",
    }
    req = httpx.Request("GET", "http://ehr:8000/patients/p1")

    def fake_get(url, params=None, **kwargs):
        assert "p1" in url
        assert params and params.get("export_type") == "full"
        return httpx.Response(200, json=response_data, request=req)

    with patch("app.services.ehr_client.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get = fake_get
        bundle = get_patient_bundle_from_service("http://ehr:8000", "p1", "full")
        assert bundle is not None
        assert bundle.patient_id == "p1"
        assert bundle.ehr_text == "Timeline content here."


def test_get_patient_bundle_from_service_404():
    """get_patient_bundle_from_service returns None on 404."""
    req = httpx.Request("GET", "http://ehr:8000/patients/nonexistent")
    with patch("app.services.ehr_client.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get.return_value = (
            httpx.Response(404, request=req)
        )
        bundle = get_patient_bundle_from_service(
            "http://ehr:8000", "nonexistent", "full"
        )
        assert bundle is None
