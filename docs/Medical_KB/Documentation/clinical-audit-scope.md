# Clinical Audit Scope (Sample Documentation)

## Purpose

This document defines the scope of the MedAudit clinical quality audit. The system performs **quality audits only** — it does **not** diagnose patients or recommend treatments. Audits identify mismatches, omissions, and continuity failures against institutional guidelines and SOPs.

## MVP Audit Pillars

1. **Imaging & Clinical Dissonance Audits**
   - Compare imaging orders, reports, and clinical documentation for consistency.
   - Flag cases where imaging findings are not reflected in clinical notes or follow-up plans.
   - Check that imaging studies have corresponding documentation (indication, result, action).

2. **Clinical Handoff & Continuity Failure Audits**
   - Identify gaps in care continuity (e.g. provider changes, site changes) where handoff may be incomplete.
   - Flag missing or delayed follow-up (e.g. medication review due, screening overdue).
   - Check that care plans and referrals are documented and have expected follow-up.

## Out of Scope (Audit Guardrails)

- **No diagnosis:** The system must not output diagnostic conclusions.
- **No treatment recommendations:** Corrective actions are process-oriented (e.g. "document follow-up plan") not clinical (e.g. "prescribe X").
- **Evidence-based only:** All findings must cite EHR or KB source; no speculation.

## Output

- Status: **NO_FINDINGS** or **FINDING_PRESENT**.
- Executive summary, risk level, findings with category/description/responsible doctor/urgency.
- Evidence snippets (KB source, EHR snippet, image reference where applicable).
- Suggested corrective actions (process/documentation only).
