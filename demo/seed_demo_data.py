#!/usr/bin/env python3
"""Seed demo audit data into a running MedArmor backend.

Usage:
    python seed_demo_data.py

Requires the `requests` library:
    pip install requests

Configuration — edit the constants below or set environment variables:
    BASE_URL        e.g. http://localhost:8000
    DEMO_USERNAME   default: demo
    DEMO_PASSWORD   default: demo
"""

import os
import random
import sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    sys.exit("requests is not installed. Run: pip install requests")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("BASE_URL", "http://localhost").rstrip("/")
USERNAME = os.environ.get("DEMO_USERNAME", "demo")
PASSWORD = os.environ.get("DEMO_PASSWORD", "demo")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login() -> str:
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print(f"[auth] Logged in as '{USERNAME}'")
    return token


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# Single-audit seed call (job + report)
# ---------------------------------------------------------------------------

def seed_one(token: str, audit: dict) -> dict:
    """Create a job (skip_celery=True) then POST the audit report for it."""
    # Step 1: create the job
    job_payload = {
        "patient_id": audit["patient_id"],
        "triggered_by": audit.get("triggered_by", "demo-seed"),
        "skip_celery": True,
        "created_at": audit.get("created_at"),
    }
    job_resp = requests.post(
        f"{BASE_URL}/api/jobs",
        json=job_payload,
        headers=_headers(token),
    )
    job_resp.raise_for_status()
    job = job_resp.json()

    # Step 2: create the audit report for that job
    findings = audit.get("findings") or []
    has_findings = bool(findings)
    report_payload = {
        "job_id": job["id"],
        "patient_id": audit["patient_id"],
        "status": audit.get("status") or ("FINDING_PRESENT" if has_findings else "NO_FINDINGS"),
        "risk_level": audit.get("risk_level"),
        "executive_summary": audit.get("executive_summary"),
        "findings": findings,
        "evidence": audit.get("evidence") or [],
        "corrective_actions": audit.get("corrective_actions") or [],
        "next_audit_date": audit.get("next_audit_date"),
        "created_at": audit.get("created_at"),
    }
    report_resp = requests.post(
        f"{BASE_URL}/api/audit-reports",
        json=report_payload,
        headers=_headers(token),
    )
    report_resp.raise_for_status()
    report = report_resp.json()

    return {
        "job_id": job["id"],
        "report_id": report["id"],
        "patient_id": audit["patient_id"],
        "status": report["status"],
    }


# ---------------------------------------------------------------------------
# Random audit generation
# ---------------------------------------------------------------------------

_FAKE_PATIENT_IDS = [
    "patient-001", "patient-002", "patient-003", "patient-004", "patient-005",
    "patient-006", "patient-007", "patient-008", "patient-009", "patient-010",
    "patient-011", "patient-012", "patient-013", "patient-014", "patient-015",
]

_FINDINGS_SAMPLES = [
    {
        "category": "Screening Gap",
        "description": "Mammogram overdue — last screening was 26 months ago, guideline requires annual screening.",
        "responsible_doctor": "Dr. Smith",
        "urgency": "high",
    },
    {
        "category": "Documentation",
        "description": "Informed consent for breast cancer screening not recorded in patient chart.",
        "responsible_doctor": "Dr. Johnson",
        "urgency": "medium",
    },
    {
        "category": "Follow-up",
        "description": "BIRADS 3 finding from prior imaging has no documented 6-month follow-up.",
        "responsible_doctor": "Dr. Patel",
        "urgency": "high",
    },
]

_CORRECTIVE_ACTIONS_SAMPLES = [
    "Schedule mammogram within 30 days",
    "Obtain and document signed informed consent",
    "Arrange 6-month follow-up imaging",
    "Notify patient of overdue screening via portal",
    "Review guideline adherence at next team meeting",
]

_SUMMARIES_NO_FINDINGS = [
    "Patient is up-to-date on all breast cancer screening requirements. No corrective action needed.",
    "Audit complete — all screening milestones met and documented within guideline windows.",
    "Full compliance confirmed. Mammogram, consent, and follow-up records are current.",
]

_SUMMARIES_FINDING_PRESENT = [
    "Audit identified one or more gaps in breast cancer screening compliance. Corrective action required.",
    "Screening documentation is incomplete. Immediate follow-up recommended.",
    "Guideline adherence issues detected. Please review findings and schedule outstanding screenings.",
]


def _make_random_audit(patient_id: str, days_ago: int) -> dict:
    """Build a NO_FINDINGS audit payload."""
    now = datetime.now(tz=timezone.utc)
    created_at = (now - timedelta(days=days_ago)).isoformat()
    return {
        "patient_id": patient_id,
        "triggered_by": "demo-seed",
        "risk_level": "low",
        "executive_summary": random.choice(_SUMMARIES_NO_FINDINGS),
        "findings": [],
        "next_audit_date": (now + timedelta(days=365)).isoformat(),
        "created_at": created_at,
    }


# ---------------------------------------------------------------------------
# Audit definitions
# Edit these lists to control exactly what appears on the findings page.
# ---------------------------------------------------------------------------

# Audits with one or more findings
AUDITS_WITH_FINDINGS = [
    {
        # Justine412 Garnett735 Schoen8
        # Cancer dx 2023-07-23 (BI-RADS 6 / Stage IA). Lumpectomy 2023-08-03,
        # chemo 2023-08 through 2024-01. Surveillance mammogram 2024-12-10
        # returned "Improving" → BI-RADS 3 (short-interval follow-up required).
        # 12-month follow-up was due by 2025-12-10; not yet completed as of today.
        "patient_id": "118012_justine412_garnett735_schoen8",
        "triggered_by": "demo-seed",
        "created_at": "2026-02-19T10:00:00+00:00",
        "risk_level": "high",
        "executive_summary": (
            "Post-treatment surveillance mammogram is overdue for this breast cancer survivor. "
            "The 2024-12-10 surveillance mammogram returned BI-RADS 3 (short-interval follow-up), "
            "requiring a repeat mammogram within 12 months (by 2025-12-10). As of 2026-02-19, "
            "no subsequent breast imaging is documented — 71 days past the follow-up deadline. "
            "Immediate scheduling is required per NCCN and ACR post-treatment surveillance guidelines."
        ),
        "findings": [
            {
                "category": "Screening Gap",
                "description": (
                    "Surveillance mammogram overdue. Patient completed active breast cancer "
                    "treatment (lumpectomy 2023-08-03, chemotherapy through 2024-01-12) for "
                    "Stage IA invasive ductal carcinoma (ER+/PR+/HER2−). Surveillance mammogram "
                    "on 2024-12-10 returned BI-RADS 3 — 'Improving' but not resolved — requiring "
                    "a follow-up mammogram within 12 months (due by 2025-12-10). Chart review on "
                    "2026-02-19 shows no subsequent breast imaging has been ordered or completed. "
                    "Patient is now 71 days beyond the follow-up window."
                ),
                "responsible_doctor": "Dr. Bennett146 Rippin620",
                "urgency": "high",
            },
        ],
        "evidence": [
            {
                "kb_source": "NCCN Clinical Practice Guidelines — Breast Cancer Survivorship (2024): post-treatment surveillance mammography annually or per BI-RADS follow-up schedule",
                "ehr_snippet": (
                    "2024-12-10: Mammography (screening surveillance). "
                    "Observation: Response to cancer treatment — Improving. "
                    "BI-RADS 3. Follow-up mammogram recommended within 12 months. "
                    "No subsequent mammogram or imaging order found in chart as of 2026-02-19."
                ),
                "image_ref": None,
            },
            {
                "kb_source": "ACR BI-RADS Atlas 5th Edition — Category 3 (Probably Benign): short-interval follow-up (6–12 months) required until stability demonstrated",
                "ehr_snippet": (
                    "Most recent post-treatment visits: 2025-03-30 (physical exam), "
                    "2025-07-06 (physical exam), 2025-11-01 (physical exam + gynecology). "
                    "None include breast imaging or imaging referral documentation."
                ),
                "image_ref": None,
            },
        ],
        "corrective_actions": [
            "Order surveillance mammogram immediately — patient is 71 days past the BI-RADS 3 follow-up deadline",
            "Contact patient by phone and patient portal to schedule imaging within 7 days",
            "Document imaging referral and patient notification in EHR",
            "Flag chart for oncology team review at next visit",
        ],
        "next_audit_date": "2026-08-19T00:00:00",
    },
    {
        # Richelle340 Wiegand701
        # Regular preventive care history (annual exams, flu shots, 2017–2025).
        # 2026-01-27: Screening mammogram + bilateral ultrasound at Brigham & Women's
        # found a 1.2 cm irregular hypoechoic mass, left breast upper outer quadrant.
        # BI-RADS 4B (moderately suspicious). Biopsy required within 2 weeks (by 2026-02-10).
        # No biopsy documented as of 2026-02-19 — 9 days overdue.
        "patient_id": "116197_richelle340_wiegand701",
        "triggered_by": "demo-seed",
        "created_at": "2026-02-19T10:00:00+00:00",
        "risk_level": "high",
        "executive_summary": (
            "Tissue biopsy is overdue following a BI-RADS 4B (moderately suspicious) finding on "
            "2026-01-27. Screening mammography and targeted ultrasound at Brigham & Women's Hospital "
            "identified a 1.2 cm irregular hypoechoic solid mass in the left breast upper outer "
            "quadrant. ACR guidelines require tissue sampling within 2 weeks for BI-RADS 4B; "
            "the action deadline of 2026-02-10 has passed with no biopsy scheduled or performed. "
            "Patient is now 9 days overdue. Immediate outreach and biopsy scheduling required."
        ),
        "findings": [
            {
                "category": "Follow-up Gap",
                "description": (
                    "Core needle biopsy not performed following BI-RADS 4B finding. "
                    "On 2026-01-27, screening mammography and targeted bilateral ultrasound at "
                    "Brigham & Women's Hospital identified a 1.2 cm irregular hypoechoic solid mass "
                    "in the left breast upper outer quadrant (BI-RADS Category 4B — moderately "
                    "suspicious, ~15–30% malignancy risk). ACR BI-RADS guidelines require tissue "
                    "sampling within 2 weeks. The deadline of 2026-02-10 has passed; no biopsy "
                    "appointment, referral, or patient contact regarding the finding is documented "
                    "in the chart as of 2026-02-19 — 9 days overdue."
                ),
                "responsible_doctor": "Dr. Almeda560 Okuneva707",
                "urgency": "high",
            },
        ],
        "evidence": [
            {
                "kb_source": "ACR BI-RADS Atlas 5th Edition — Category 4B (Moderately Suspicious): tissue sampling required, typically within 2 weeks of finding",
                "ehr_snippet": (
                    "2026-01-27: Screening mammography + bilateral breast ultrasound, "
                    "Brigham & Women's Hospital. "
                    "Finding: 1.2 cm irregular hypoechoic solid mass, left breast upper outer quadrant. "
                    "Observation: BI-RADS Category 4 — Suspicious Abnormality. "
                    "Recommendation: Core needle biopsy. "
                    "No biopsy order, scheduling note, or patient contact documented as of 2026-02-19."
                ),
                "image_ref": None,
            },
            {
                "kb_source": "USPSTF / ACR follow-up protocol: BI-RADS 4B requires biopsy within 2 weeks to rule out malignancy",
                "ehr_snippet": (
                    "Prior history: routine preventive visits 2017, 2019, 2021, 2023, 2025 — "
                    "no prior breast complaints, no family history of breast cancer documented. "
                    "No previous abnormal mammogram on file. PCP: Dr. Ernest565 Runte676, "
                    "Signature Healthcare Medical Group."
                ),
                "image_ref": None,
            },
        ],
        "corrective_actions": [
            "Schedule core needle biopsy immediately — patient is 9 days past the BI-RADS 4B 2-week action window",
            "Contact patient by phone and portal message today to arrange biopsy within 48 hours",
            "Notify PCP Dr. Ernest565 Runte676 of the overdue follow-up",
            "Escalate to supervising radiologist if biopsy cannot be arranged within 48 hours",
            "Document all patient contact attempts in EHR",
        ],
        "next_audit_date": "2026-03-05T00:00:00",
    },
]

# Audits with no findings — using real patients from the EHR dataset
AUDITS_NO_FINDINGS = [
    {
        "patient_id": "16951_beatris270_elaina826_homenick806",
        "triggered_by": "demo-seed",
        "risk_level": "low",
        "executive_summary": (
            "Full compliance confirmed. Annual mammogram completed on schedule, "
            "informed consent is current, and all follow-up items are resolved. "
            "No corrective action required."
        ),
        "findings": [],
        "next_audit_date": "2027-02-19T00:00:00",
    },
    {
        "patient_id": "17857_becky854_rebbeca432_sipes176",
        "triggered_by": "demo-seed",
        "risk_level": "low",
        "executive_summary": (
            "Audit complete — all breast cancer screening milestones met and documented "
            "within guideline windows. Mammogram up to date, consent on file. "
            "No corrective action required."
        ),
        "findings": [],
        "next_audit_date": "2027-02-19T00:00:00",
    },
]

# Number of additional random NO_FINDINGS audits to generate
RANDOM_COUNT = 521

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    token = login()
    now = datetime.now(tz=timezone.utc)

    # Spread explicit audits evenly across the last 30 days
    explicit_base = AUDITS_WITH_FINDINGS + AUDITS_NO_FINDINGS
    total_explicit = len(explicit_base)
    all_explicit = []
    for i, audit in enumerate(explicit_base):
        days_ago = int(30 * (total_explicit - i) / total_explicit)
        all_explicit.append({
            **audit,
            # Preserve a created_at already set in the audit definition (e.g. for
            # findings-present audits that must post-date the clinical event).
            "created_at": audit.get("created_at") or (now - timedelta(days=days_ago)).isoformat(),
        })

    # Spread random audits across the last 30 days
    patient_pool = (_FAKE_PATIENT_IDS * (RANDOM_COUNT // len(_FAKE_PATIENT_IDS) + 1))
    random.shuffle(patient_pool)
    random_audits = [
        _make_random_audit(patient_pool[i], days_ago=random.randint(0, 30))
        for i in range(RANDOM_COUNT)
    ]

    all_audits = all_explicit + random_audits
    explicit_count = len(all_explicit)

    explicit_results = []
    for i, audit in enumerate(all_audits, start=1):
        result = seed_one(token, audit)
        if i <= explicit_count:
            explicit_results.append(result)
        print(f"[seed] {i}/{len(all_audits)}  patient={result['patient_id']}  status={result['status']}")

    print(
        f"\n[seed]  Total seeded : {len(all_audits)} "
        f"({RANDOM_COUNT} random, {explicit_count} explicit)"
    )

    for audit in explicit_results:
        url = f"{FRONTEND_URL}/audits/reports/{audit['report_id']}"
        print(
            f"[audit] patient={audit['patient_id']}  status={audit['status']}\n"
            f"        {url}"
        )

    print("\nDone. Refresh the dashboard to see updated counts.")


if __name__ == "__main__":
    main()
