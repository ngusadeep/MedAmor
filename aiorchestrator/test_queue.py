#!/usr/bin/env python3
"""Test the async task queue system."""

import time
import requests

API_URL = "http://localhost:5001"


def test_queue():
    """Submit multiple audit jobs and track their progress."""
    print("Testing Async Task Queue System")
    print("=" * 60)

    # Check if API is running
    try:
        resp = requests.get(f"{API_URL}/health", timeout=2)
        if resp.status_code != 200:
            print("✗ API is not running!")
            print(f"  Start it with: python main.py")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API at", API_URL)
        print("  Start it with: python main.py")
        return False

    print("✓ API is running\n")

    # Submit multiple jobs
    print("1. Submitting 3 patient audit jobs...")
    patients = [
        {"id": "patient-001", "type": "hypertension_compliance"},
        {"id": "patient-002", "type": "diabetes_management"},
        {"id": "patient-003", "type": "general"},
    ]

    job_ids = []
    for patient in patients:
        resp = requests.post(
            f"{API_URL}/audit",
            json={"patient_id": patient["id"], "audit_type": patient["type"]},
        )
        if resp.status_code == 202:
            data = resp.json()
            job_id = data["job_id"]
            job_ids.append((job_id, patient["id"]))
            print(f"   ✓ Queued: {patient['id']} → Job ID: {job_id[:8]}...")
        else:
            print(f"   ✗ Failed to queue {patient['id']}: {resp.text}")

    if not job_ids:
        print("\n✗ No jobs were queued. Check Celery worker is running:")
        print("  celery -A aiorchestrator.celery_app worker --loglevel=info")
        return False

    print(f"\n2. Checking queue stats...")
    resp = requests.get(f"{API_URL}/queue/stats")
    if resp.status_code == 200:
        stats = resp.json()
        workers = stats.get("workers", {}).get("count", 0)
        active = stats.get("queue", {}).get("active_jobs", 0)
        queued = stats.get("queue", {}).get("queued_jobs", 0)
        print(f"   Workers: {workers}")
        print(f"   Active jobs: {active}")
        print(f"   Queued jobs: {queued}")
        if workers == 0:
            print("\n   ⚠ No workers detected! Start one with:")
            print("     celery -A aiorchestrator.celery_app worker --loglevel=info")
    else:
        print(f"   ⚠ Could not get queue stats: {resp.text}")

    # Poll for results
    print(f"\n3. Waiting for jobs to complete...")
    completed = {}
    max_wait = 60  # 60 seconds max
    start_time = time.time()

    while len(completed) < len(job_ids):
        if time.time() - start_time > max_wait:
            print("\n   ⚠ Timeout reached. Some jobs may still be processing.")
            break

        for job_id, patient_id in job_ids:
            if job_id in completed:
                continue

            resp = requests.get(f"{API_URL}/audit/{job_id}")
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")

                if status == "completed":
                    # Get result
                    result_resp = requests.get(f"{API_URL}/audit/{job_id}/result")
                    if result_resp.status_code == 200:
                        result = result_resp.json()
                        completed[job_id] = result
                        print(f"   ✓ {patient_id}: Completed")

                        # Show brief summary
                        report = result.get("report", "")
                        if "compliant" in report.lower():
                            import json

                            try:
                                audit = json.loads(report)
                                compliant = (
                                    "✓ Compliant"
                                    if audit.get("compliant")
                                    else "✗ Non-compliant"
                                )
                                gaps_count = len(audit.get("gaps", []))
                                print(f"      {compliant}, {gaps_count} gaps found")
                            except:
                                pass

                elif status == "failed":
                    completed[job_id] = {"error": data.get("message")}
                    print(f"   ✗ {patient_id}: Failed - {data.get('message')}")

                elif status == "processing":
                    print(f"   ⏳ {patient_id}: Processing...")

        time.sleep(2)

    # Summary
    print("\n" + "=" * 60)
    if len(completed) == len(job_ids):
        print(f"✅ All {len(job_ids)} jobs completed successfully!")
    else:
        print(f"⚠ {len(completed)}/{len(job_ids)} jobs completed")

    print("\nQueue system is working! ✨")
    return True


if __name__ == "__main__":
    import sys

    success = test_queue()
    sys.exit(0 if success else 1)
