#!/usr/bin/env python3
"""Test the complete audit workflow end-to-end.

Usage:
    python test_workflow.py [patient_id] [audit_type]

Examples:
    python test_workflow.py 26171 hypertension_compliance
    python test_workflow.py test-patient general
"""

import json
import sys

from dotenv import load_dotenv

load_dotenv()

from aiorchestrator.app.agent import build_audit_graph


def test_audit(patient_id: str = "test-patient", audit_type: str = "general"):
    """Run a complete audit workflow and print the results."""
    print(f"Testing MedAudit Workflow")
    print(f"Patient ID: {patient_id}")
    print(f"Audit Type: {audit_type}")
    print("-" * 60)

    # Build the LangGraph
    print("\n1. Building LangGraph workflow...")
    graph = build_audit_graph()
    print("   ✓ Graph compiled")

    # Run the audit
    print("\n2. Executing audit workflow...")
    print("   → Fetching FHIR data...")
    print("   → Retrieving relevant guidelines...")
    print("   → Generating audit report with Gemini...")

    try:
        result = graph.invoke(
            {
                "patient_id": patient_id,
                "audit_type": audit_type,
            }
        )

        print("   ✓ Workflow complete")

        # Display results
        print("\n3. Audit Results:")
        print("-" * 60)

        # Parse and pretty-print the report
        report = json.loads(result.get("report", "{}"))
        print(
            f"\nCompliance Status: {'✓ COMPLIANT' if report.get('compliant') else '✗ NON-COMPLIANT'}"
        )

        gaps = report.get("gaps", [])
        if gaps:
            print(f"\nIdentified Gaps ({len(gaps)}):")
            for i, gap in enumerate(gaps, 1):
                print(f"  {i}. {gap}")

        evidence = report.get("evidence", [])
        if evidence:
            print(f"\nEvidence ({len(evidence)}):")
            for i, item in enumerate(evidence, 1):
                print(f"\n  {i}. Guideline: {item.get('guideline')}")
                print(f"     Violation: {item.get('violation')}")

        # Show sources
        sources = result.get("context", [])
        if sources:
            print(f"\n\nRetrieved Guidelines ({len(sources)} chunks):")
            for i, source in enumerate(sources[:3], 1):  # Show first 3
                preview = source[:100] + "..." if len(source) > 100 else source
                print(f"  {i}. {preview}")

        print("\n" + "-" * 60)
        print("Test completed successfully!")
        return True

    except Exception as e:
        print(f"\n✗ Error during workflow execution:")
        print(f"  {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    patient_id = sys.argv[1] if len(sys.argv) > 1 else "test-patient"
    audit_type = sys.argv[2] if len(sys.argv) > 2 else "general"

    success = test_audit(patient_id, audit_type)
    sys.exit(0 if success else 1)
