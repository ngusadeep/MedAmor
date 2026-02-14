# MedAudit — Frequently Asked Questions (Sample)

## What does MedAudit do?

MedAudit runs **clinical quality audits** on EHR data. It checks for mismatches, omissions, and continuity failures (e.g. imaging not documented in notes, handoff gaps, medication review due but not done). It does **not** diagnose patients or recommend treatments.

## What are "Imaging & Clinical Dissonance" audits?

These audits compare imaging studies and reports with clinical documentation. If an imaging result is significant but not reflected in subsequent notes or follow-up plans, the system flags it as a potential dissonance for human review.

## What are "Clinical Handoff & Continuity Failure" audits?

These look for gaps when care moves between providers or sites: missing handoff notes, "medication review due" or "referral" with no documented follow-up, or screening indicated but not completed/deferred.

## What is the output format?

Each audit produces a structured payload: job ID, patient ID, status (NO_FINDINGS or FINDING_PRESENT), executive summary, findings (with category, description, responsible doctor, urgency), evidence snippets, and suggested corrective actions. Corrective actions are process-oriented (e.g. "document follow-up") not clinical.

## How is the knowledge base used?

Guidelines, SOPs, and policies in the Medical_KB (Documentation, SOPs, User_Manuals, FAQs) are embedded and retrieved (RAG) so the AI audit is **grounded** in your institution’s rules. Findings should cite KB or EHR evidence.

## Is MedGemma used for diagnosis?

No. MedGemma is used only to **analyze** text (and optionally images) for **audit** purposes: comparing record to guidelines, flagging inconsistencies, and summarizing evidence. Diagnosis and treatment remain the responsibility of clinicians.
