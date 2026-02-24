SYSTEM CONTEXT & USAGE INSTRUCTIONS

This document serves as a structured knowledge base for the Breast Imaging Reporting and Data System (BI-RADS). It is designed for natural language processing (NLP), electronic health record (EHR) text extraction, FHIR resource mapping (DiagnosticReport, Observation, ImagingStudy), and automated clinical decision support.

When evaluating narrative imaging notes, use the EHR / FHIR Text Cues and Imaging Features to infer the correct BI-RADS classification and recommend the corresponding Clinical Action / Follow-up.

BI-RADS Category 0

Assessment: Incomplete Evaluation

Malignancy Probability: N/A (Insufficient data)

Clinical Meaning: Findings are unclear. The radiologist requires more images or prior images to determine a final diagnostic score.

Imaging Features / Typical Reasons:

Need for prior comparison

Need for additional views (e.g., spot compression, magnification)

Need for ultrasound or MRI correlation

EHR / FHIR Text Cues:

"Additional imaging recommended"

"Comparison with prior studies needed"

"Incomplete evaluation"

"Recall for diagnostic mammography"

Presence of orders for an additional modality without a final assessment

Clinical Action / Follow-up: * Conduct additional mammograms or ultrasound within 30 days.

Obtain and compare past mammogram images to look for tissue changes.

BI-RADS Category 1

Assessment: Negative

Malignancy Probability: 0%

Clinical Meaning: Breast tissue appears completely normal. There are no findings of concern.

Imaging Features / Typical Reasons:

Symmetric tissue

Complete absence of masses, calcifications, or architectural asymmetry

Healthy breast tissue

EHR / FHIR Text Cues:

"No suspicious mass, calcification, or architectural distortion"

"Negative mammogram"

"Unremarkable"

Clinical Action / Follow-up: * Routine screening mammography every 2 years.

BI-RADS Category 2

Assessment: Benign

Malignancy Probability: 0%

Clinical Meaning: Findings are present but are unambiguously non-cancerous.

Imaging Features / Typical Reasons:

Simple cysts

Intramammary lymph nodes

Fat necrosis

Stable benign calcifications

Fibroadenomas (classic appearance)

Scar tissue

Non-cancerous breast development

EHR / FHIR Text Cues:

"Benign-appearing"

"Simple cyst"

"Fat-containing lesion"

"Involuting fibroadenoma"

"Stable for >2 years"

Clinical Action / Follow-up: * Continued monitoring with routine screening mammography every 1 year.

BI-RADS Category 3

Assessment: Probably Benign

Malignancy Probability: < 2%

Clinical Meaning: A finding is present that is highly likely to be benign, but requires establishing stability over time to rule out malignancy entirely.

Imaging Features / Typical Reasons:

New but likely benign mass

Clustered punctate calcifications

Focal asymmetry without suspicious features

EHR / FHIR Text Cues:

"Probably benign"

"6-month follow-up recommended"

"Short-interval follow-up"

"Low suspicion"

Clinical Action / Follow-up: * Short-interval follow-up mammogram in 6 months.

Followed by subsequent screenings at 12 months and 24 months.

If the mass remains completely stable over this 2-year period, revert to routine 24-month screening.

BI-RADS Category 4A

Assessment: Suspicious (Low Suspicion)

Malignancy Probability: 2% to 10%

Clinical Meaning: Findings are suspicious enough to warrant a biopsy, but the likelihood of cancer is low.

Imaging Features / Typical Reasons:

Small mass

Mostly circumscribed margins

Mildly suspicious calcifications

EHR / FHIR Text Cues:

"Low suspicion for malignancy"

"Biopsy recommended for confirmation"

"Indeterminate mass"

"Circumscribed margins" or "Partially obscured margins"

Clinical Action / Follow-up: * Image-guided core biopsy scheduled (non-urgent), target within 2 to 4 weeks.

BI-RADS Category 4B

Assessment: Suspicious (Moderate Suspicion)

Malignancy Probability: 10% to 50%

Clinical Meaning: Clearly abnormal morphology that is concerning for cancer, though lacks the classic appearance of a definitive malignancy.

Imaging Features / Typical Reasons:

Irregular mass

Non-circumscribed margins

Heterogeneous density

New or enlarging lesion

EHR / FHIR Text Cues:

"Suspicious mass"

"Irregular shape"

"Indistinct margins"

"Moderate concern for malignancy"

"Unspecified BI-RADS 4"

Clinical Action / Follow-up: * Image-guided core biopsy scheduled at the next available opportunity, target within 1 to 2 weeks.

BI-RADS Category 4C

Assessment: Suspicious (High Suspicion)

Malignancy Probability: 50% to 95%

Clinical Meaning: Findings highly resemble cancer but are not yet proven.

Imaging Features / Typical Reasons:

Spiculated margins

Marked architectural distortion

Pleomorphic or linear calcifications

Associated skin or nipple changes

EHR / FHIR Text Cues:

"Highly suspicious"

"Spiculated mass"

"Architectural distortion"

"Pleomorphic calcifications"

Clinical Action / Follow-up: * Urgent biopsy within days, maximum timeframe of 1 week.

BI-RADS Category 4D (Metadata / Non-Standard)

Assessment: Suspicious (Very High Suspicion / Near 5)

Malignancy Probability: ~95%

Clinical Meaning: Note: This is an informal, non-standardized sub-classification used by some institutions to describe findings that stop just short of BI-RADS 5.

EHR / FHIR Text Cues:

"Very high suspicion"

"Strongly concerning for malignancy"

Biopsy framed as highly urgent

Clinical Action / Follow-up: * Treat identically to 4C/5: Urgent biopsy required immediately.

BI-RADS Category 5

Assessment: Highly Suggestive of Malignancy

Malignancy Probability: ≥ 95%

Clinical Meaning: The radiologist is highly confident the finding is cancerous based on classic imaging markers.

Imaging Features / Typical Reasons:

Spiculated mass

Segmental linear calcifications

Skin thickening, nipple retraction

Pathologic lymph nodes

EHR / FHIR Text Cues:

"Highly suggestive of malignancy"

"Consistent with carcinoma"

"Urgent tissue diagnosis recommended"

Clinical Action / Follow-up: * Immediate biopsy target within 24 to 72 hours.

Absolute maximum review and biopsy timeframe of 1 week.

BI-RADS Category 6

Assessment: Known Malignancy

Malignancy Probability: 100% (Proven)

Clinical Meaning: A cancer diagnosis has already been confirmed via biopsy. Current imaging is strictly for staging, surgical planning, or evaluating treatment response.

Imaging Features / Typical Reasons:

Cancer already biopsy-proven prior to imaging

Imaging done for staging or treatment response

EHR / FHIR Text Cues:

"Known biopsy-proven malignancy"

"Status post core biopsy showing..."

Presence of an existing cancer diagnosis in the patient's FHIR Condition resource.

Clinical Action / Follow-up: * Establish or continue cancer treatment plan.

Referral to Oncology.

Conduct a follow-up mammogram 6 to 12 months post-treatment to establish a new baseline and determine future surveillance scheduling.