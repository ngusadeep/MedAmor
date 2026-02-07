"""
FHIR Reader - A library for converting FHIR Bundle resources into LLM-friendly timelines.

This package provides tools to convert complex FHIR (Fast Healthcare Interoperability Resources)
data into chronological narrative formats optimized for LLM review and consistency checking.

Example usage:
    from aibroker.fhir_reader import FHIRTimelineConverter, load_and_convert

    # Simple file conversion
    timeline = load_and_convert('patient_bundle.json')
    print(timeline)

    # From FHIR API response
    import requests
    response = requests.get('http://fhir-server/Patient/123/$everything')
    bundle = response.json()
    timeline = convert_fhir_bundle_to_timeline(bundle)
"""

from .timeline import (
    FHIRTimelineConverter,
    convert_fhir_bundle_to_timeline,
    load_and_convert,
)

__all__ = [
    "FHIRTimelineConverter",
    "convert_fhir_bundle_to_timeline",
    "load_and_convert",
]

__version__ = "0.1.0"
