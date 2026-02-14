#!/usr/bin/env python3
"""Test FHIR fetching independently."""

import os
os.environ["USE_DUMMY_FHIR"] = "true"  # Start with dummy data

from aiorchestrator.app.fhir import fetch_patient_bundle, format_patient_summary

print("Testing FHIR functionality...")
print("-" * 60)

# Test 1: Dummy data
print("\n1. Testing with DUMMY data:")
try:
    from aiorchestrator.app.agent import DUMMY_FHIR_BUNDLE
    summary = format_patient_summary(DUMMY_FHIR_BUNDLE)
    print(f"✓ Dummy data summary: {summary[:100]}...")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Real FHIR (will fail if server not running, but that's OK)
print("\n2. Testing REAL FHIR fetching:")
print("   Note: This will fail if HAPI FHIR server is not running")
try:
    # First check if we have any patients
    import requests
    response = requests.get("http://localhost:9080/fhir/Patient?_count=1", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if data.get("entry"):
            patient_id = data["entry"][0]["resource"]["id"]
            print(f"   Found patient: {patient_id}")

            bundle = fetch_patient_bundle(patient_id)
            print(f"✓ Successfully fetched FHIR bundle for patient {patient_id}")
            print(f"  Bundle has {len(bundle.get('entry', []))} entries")

            summary = format_patient_summary(bundle)
            print(f"  Summary: {summary[:150]}...")
        else:
            print("⚠ No patients in FHIR server. Upload data first:")
            print("   cd ehr && ./upload_fhir.sh data/breast/fhir/")
    else:
        print(f"⚠ FHIR server returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("⚠ Cannot connect to FHIR server at localhost:9080")
    print("  Start it with: docker compose up hapi_fhir hapi_db -d")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "-" * 60)
print("Test complete!")
