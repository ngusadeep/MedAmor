#!/usr/bin/env python3
"""Test breast cancer screening audit with real patient case.

Patient: Mrs. Justine Garnett (39b7de4b-abf2-d772-461e-193e503a035b)
Scenario: Breast cancer diagnosed in 2023, follow-up screening in 2024
"""

import os
os.environ['USE_DUMMY_FHIR'] = 'false'  # We'll use real FHIR or create a bundle

from dotenv import load_dotenv
load_dotenv()

from aiorchestrator.app.agent import build_audit_graph
import json


# Create a FHIR-like summary based on the patient timeline
JUSTINE_FHIR_SUMMARY = {
    "resourceType": "Bundle",
    "type": "collection",
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "39b7de4b-abf2-d772-461e-193e503a035b",
                "name": [{"given": ["Justine412"], "family": "Schoen8"}],
                "birthDate": "1979-02-12",
                "gender": "female",
            }
        },
        {
            "resource": {
                "resourceType": "Condition",
                "id": "breast-cancer-1",
                "code": {
                    "coding": [{
                        "display": "Malignant neoplasm of breast (disorder)",
                        "code": "254837009"
                    }]
                },
                "clinicalStatus": {
                    "coding": [{
                        "code": "active"
                    }]
                },
                "onsetDateTime": "2023-07-23",
                "note": [{
                    "text": "Stage IA breast cancer. Tumor size 0.48 cm. cT1cN0cM0. ER+/PR+/HER2-"
                }]
            }
        },
        {
            "resource": {
                "resourceType": "Procedure",
                "id": "initial-mammogram",
                "code": {
                    "coding": [{
                        "display": "Screening mammography (procedure)",
                        "code": "71651007"
                    }]
                },
                "status": "completed",
                "performedDateTime": "2023-07-23",
                "note": [{
                    "text": "Screening mammography performed. Suspicious findings led to same-day ultrasound and biopsy."
                }]
            }
        },
        {
            "resource": {
                "resourceType": "Procedure",
                "id": "biopsy",
                "code": {
                    "coding": [{
                        "display": "Biopsy of breast (procedure)",
                        "code": "122548005"
                    }]
                },
                "status": "completed",
                "performedDateTime": "2023-07-23",
                "note": [{
                    "text": "Core needle biopsy confirmed malignancy"
                }]
            }
        },
        {
            "resource": {
                "resourceType": "Procedure",
                "id": "lumpectomy",
                "code": {
                    "coding": [{
                        "display": "Lumpectomy of breast (procedure)",
                        "code": "392021009"
                    }]
                },
                "status": "completed",
                "performedDateTime": "2023-08-03"
            }
        },
        {
            "resource": {
                "resourceType": "Procedure",
                "id": "chemotherapy-1",
                "code": {
                    "coding": [{
                        "display": "Chemotherapy (procedure)",
                        "code": "367336001"
                    }]
                },
                "status": "completed",
                "performedPeriod": {
                    "start": "2023-08-12",
                    "end": "2024-01-12"
                },
                "note": [{
                    "text": "8 cycles of adjuvant chemotherapy with Doxorubicin"
                }]
            }
        },
        {
            "resource": {
                "resourceType": "Procedure",
                "id": "followup-mammogram",
                "code": {
                    "coding": [{
                        "display": "Mammography (procedure)",
                        "code": "71651007"
                    }]
                },
                "status": "completed",
                "performedDateTime": "2024-12-10",
                "note": [{
                    "text": "Post-treatment surveillance mammography performed 16 months after diagnosis"
                }]
            }
        },
        {
            "resource": {
                "resourceType": "Observation",
                "id": "treatment-response",
                "code": {
                    "coding": [{
                        "display": "Response to cancer treatment",
                        "code": "395100000"
                    }]
                },
                "status": "final",
                "valueCodeableConcept": {
                    "coding": [{
                        "display": "Improving (qualifier value)",
                        "code": "385633008"
                    }]
                },
                "effectiveDateTime": "2024-12-10"
            }
        }
    ]
}


def test_breast_cancer_screening_audit():
    """Test breast cancer screening audit with Justine's case."""
    print("=" * 80)
    print("BREAST CANCER SCREENING AUDIT - PATIENT CASE TEST")
    print("=" * 80)

    print("\nPatient: Mrs. Justine Garnett")
    print("DOB: 1979-02-12 (Age: 45)")
    print("Timeline:")
    print("  - 2023-07-23: Initial screening → Biopsy → Breast cancer diagnosis (Stage IA)")
    print("  - 2023-08-03: Lumpectomy")
    print("  - 2023-08-12 to 2024-01-12: 8 cycles chemotherapy")
    print("  - 2024-12-10: Post-treatment surveillance mammography (16 months post-dx)")
    print()

    # Build the audit graph
    print("Building audit workflow...")
    graph = build_audit_graph()

    # Inject the patient's FHIR data
    print("Running breast cancer screening audit...")
    print()

    # We'll manually inject the FHIR data to test without needing HAPI server
    from aiorchestrator.app.fhir import format_patient_summary
    from aiorchestrator.app.vector_store import get_vector_store
    from langchain_google_genai import ChatGoogleGenerativeAI
    from aiorchestrator.app.agent import AuditReport

    # Format patient summary with enhanced details
    patient_summary = f"""
Patient: Justine412 Schoen8 (ID: 39b7de4b-abf2-d772-461e-193e503a035b)
DOB: 1979-02-12 (Age 45 years)
Gender: Female

BREAST CANCER HISTORY:
- 2023-07-23: Initial screening mammography performed → Suspicious findings detected
- 2023-07-23: Same-day ultrasound and core needle biopsy → Malignancy confirmed
- 2023-07-23: Diagnosis - Malignant neoplasm of breast (Stage IA, cT1cN0cM0)
  * Tumor size: 0.48 cm
  * ER+/PR+/HER2-
  * No lymph node involvement

TREATMENT TIMELINE:
- 2023-08-03: Lumpectomy performed (11 days after diagnosis)
- 2023-08-12 to 2024-01-12: Adjuvant chemotherapy (8 cycles Doxorubicin over 5 months)
- 2024-01-16: Started hormonal therapy (Tamoxifen + Abemaciclib)

POST-TREATMENT SURVEILLANCE:
- 2024-05-05: Postoperative follow-up (10 months post-diagnosis)
- 2024-08-15: Postoperative follow-up (13 months post-diagnosis)
- 2024-12-10: Surveillance mammography performed (16.5 months post-diagnosis, 11 months after chemotherapy completion)
- 2024-12-10: Treatment response: Improving

CURRENT STATUS (2024-12-10):
- Active condition: Malignant neoplasm of breast
- On hormonal therapy
- Regular surveillance ongoing
"""
    print("Patient Summary:")
    print("-" * 80)
    print(patient_summary)
    print()

    # Retrieve guidelines
    print("Retrieving breast cancer screening guidelines...")
    vs = get_vector_store()
    query = f"breast cancer screening BI-RADS follow-up post-treatment surveillance: {patient_summary}"
    docs = vs.similarity_search(query, k=5)
    guidelines = "\n\n".join([d.page_content for d in docs])
    print(f"✓ Retrieved {len(docs)} guideline chunks")
    print()

    # Generate audit report
    print("Generating audit with Gemini...")
    llm = ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        temperature=0,
    )

    structured_llm = llm.with_structured_output(AuditReport)

    prompt = f"""You are an expert Medical Auditor specializing in breast cancer screening compliance.

Audit the patient's breast cancer screening and follow-up care against BI-RADS guidelines.

## Patient History
{patient_summary}

## Breast Cancer Screening Guidelines (BI-RADS)
{guidelines}

## Key Guidelines to Check:
1. BI-RADS Category 6 (Known malignancy): After treatment completion, surveillance mammography should be performed within 6-12 months
2. Appropriate timing of follow-up imaging after cancer diagnosis and treatment
3. Adequate post-treatment surveillance

## Instructions
1. Determine if the patient's screening and follow-up schedule complies with BI-RADS guidelines
2. Identify any gaps in care timing or missing screenings
3. For each gap, cite the specific guideline and violation

Output ONLY valid JSON with this structure:
{{"compliant": boolean, "gaps": ["string"], "evidence": [{{"guideline": "string", "violation": "string"}}]}}"""

    try:
        result = structured_llm.invoke(prompt)
        report = {
            "compliant": result.compliant,
            "gaps": result.gaps,
            "evidence": [{"guideline": e.guideline, "violation": e.violation} for e in result.evidence],
        }

        print("=" * 80)
        print("AUDIT RESULTS")
        print("=" * 80)
        print()

        status = "✓ COMPLIANT" if report["compliant"] else "✗ NON-COMPLIANT"
        print(f"Status: {status}")
        print()

        if report["gaps"]:
            print(f"Identified Gaps ({len(report['gaps'])}):")
            for i, gap in enumerate(report["gaps"], 1):
                print(f"  {i}. {gap}")
            print()

        if report["evidence"]:
            print(f"Evidence ({len(report['evidence'])} findings):")
            for i, item in enumerate(report["evidence"], 1):
                print(f"\n  {i}. Guideline: {item['guideline']}")
                print(f"     Violation: {item['violation']}")

        print()
        print("=" * 80)
        print("✅ Breast Cancer Screening Audit Complete!")
        print("=" * 80)

        return report

    except Exception as e:
        print(f"✗ Error during audit: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_breast_cancer_screening_audit()
