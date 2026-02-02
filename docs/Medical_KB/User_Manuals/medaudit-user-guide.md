# MedAudit Platform — User Guide (Sample)

## 1. Logging In

- Use your institutional credentials. The platform uses JWT authentication; session is maintained until logout or expiry.

## 2. Dashboard

- The main dashboard shows **historical audits** in a table.
- Columns typically include: Job ID, Patient ID, Date, Status (No Findings / Findings Present), Risk Level.
- Use filters or search to find a specific patient or time range.

## 3. Triggering a Manual Audit

- Use the **Manual Review** form to request an audit for a patient.
- Provide the **Patient ID** (and optionally select export type or date range).
- Submit; the job is queued. Status will show "Pending" until the audit completes.
- Refresh or use polling to see the result; then open the audit detail view.

## 4. Audit Detail View

- Click a row in the audits table to open the full report.
- You will see:
  - **Executive summary**
  - **Findings** (category, description, responsible doctor, urgency)
  - **Evidence** (KB source, EHR snippet, image reference)
  - **Suggested corrective actions** (process/documentation only — no clinical recommendations)

## 5. Expected Follow-up and Next Audit

- Some reports include **date of expected follow-up** or **next AI audit**.
- Use this to plan the next review or to trigger a scheduled audit.

## 6. Security and Compliance

- All actions are logged. The system does not diagnose; it performs quality audits only.
- PHI is protected per institutional policy; do not share audit output outside authorized channels.
