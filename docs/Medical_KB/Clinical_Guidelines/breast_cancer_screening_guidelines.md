NOTE: Sources at the end


Breast Screening Guidelines
Each BI-RADS category, from 0 to 6, has a specific clinical meaning and suggested follow-up care. Follow-up care recommendations are based on the outcomes of previous patients with the same scores. These recommendations apply to screening mammography unless otherwise specified.
BI-RADS Category 0
Meaning: Category 0 means the findings are unclear. The radiologist will need more images to determine a score.
Typical Reasons:
Need prior comparison
Need additional views (spot compression, magnification)
Need ultrasound or MRI correlation
Example Cues in Medical Notes:
“Additional imaging recommended”
“Comparison with prior studies needed”
“Incomplete evaluation”
“Recall for diagnostic mammography”
Orders for additional modality without a final assessment
Required Followup:
Conducting additional mammograms or an ultrasound to see different angles of the breast tissue within 30 days
Looking for changes in the breast based on comparisons of current and past mammogram images


BI-RADS Category 1
Meaning: Category 1 means the findings are negative and the breast tissue appears normal.
Typical Reasons:
No masses, no calcifications, no asymmetry
No other abnormalities have been found.
The breast tissue is deemed healthy.
Example Cues in Medical Notes:
“No suspicious mass, calcification, or architectural distortion”
“Negative mammogram”
“Unremarkable”
Required Follow up:
Follow-up care calls for continued monitoring with regular mammograms every 2 years
BI-RADS Category 2
Meaning: Category 2 means the findings are present but benign, which is also negative for cancer. While a mass, calcification or other abnormality may have been detected, it’s not cancerous.
Typical Reasons:
Simple cysts
Intramammary lymph nodes
Fat necrosis
Stable benign calcifications
Fibroadenomas (classic appearance)
Scar-Tissue
Non-cancerous breast development
Example Cues in Medical Notes
“Benign-appearing”
“Simple cyst”
“Fat-containing lesion”
“Involuting fibroadenoma”
“Stable for >2 years”
Required Follow up:
Continued monitoring with regular mammograms every year.
BI-RADS Category 3
Meaning: Category 3 means the findings are probably benign (less than 2% chance of malignancy). While a mass, calcification or other abnormality may have been found, it’s most likely not cancerous.
Typical Reasons:
New but likely benign mass
Clustered punctate calcifications
Focal asymmetry without suspicious features
Example Cues in Medical Notes:
“Probably benign”
“6-month follow-up recommended”
“Short-interval follow-up”
“Low suspicion”
Required Follow up:
Follow-up care calls for another mammogram in six months to check for changes, knowing that a cancerous mass changes over time.
After the 6 months screening, there should be a 12 month screening, and a 24 month (2 year) screening.
If the mass remains stable over the next two years, they can return to regular 24 month screening
BI-RADS Category 4A
Meaning: Findings suspect cancer, though low chance of cancer (2 to 10%)
Typical Reasons:
Small mass
Mostly circumscribed margins
Mildly suspicious calcifications
Example Cues in Medical Notes
“Low suspicion for malignancy”
“Biopsy recommended for confirmation”
“Indeterminate mass”
Circumscribed or partially obscured margins
Small lesion and mostly benign morphology
Required Follow up:
Image guided core biopsy scheduled, but not urgent, can be within 2 to 4 weeks
BI-RADS Category 4B
Meaning: Findings suspect cancer, though medium chance of cancer (10 to 50%)

Typical Reasons:
Irregular mass
Non-circumscribed margins
Heterogeneous density
New or enlarging lesion
Clearly abnormal morphology, but not classic cancer
Example Cues in Medical Notes
“Suspicious mass”
“Irregular shape”
“Indistinct margins”
“Moderate concern for malignancy”
“Unspecified BI-RADS 4”
Required Follow up:
Image guided core biopsy scheduled within 1 to 2 weeks, at next available opportunity
BI-RADS Category 4C
Meaning: Findings suspect cancer with high probability of cancer (50 to 95%)
Typical Reasons:
Spiculated margins
Marked architectural distortion
Pleomorphic or linear calcifications
Associated skin or nipple changes
Example Cues in Medical Notes
“Highly suspicious”
“Spiculated mass”
“Architectural distortion”
“Pleomorphic calcifications”
Required Follow up:
Urgent biopsy within days, and no more than 1 week
BI-RADS Category 5
Meaning: The findings highly suggest cancer with a 95 percent chance or higher of being cancerous.
Typical Reasons:
Spiculated mass
Segmental linear calcifications
Skin thickening, nipple retraction
Pathologic lymph nodes
Example Cues in Medical Notes
“Highly suggestive of malignancy”
“Consistent with carcinoma”
“Urgent tissue diagnosis recommended”
Required Follow up:
Immediate biopsy if possible, target within 24–72 hours. If those timelines are not possible, it must be reviewed within 1 week.
BI-RADS Category 6
Meaning: Cancer was diagnosed using a biopsy.
Typical Reasons:
Cancer already biopsy-proven
Imaging done for staging or treatment response
Example Cues in Medical Notes
“Known biopsy-proven malignancy”
“Status post core biopsy showing…”
Existing cancer diagnosis in Condition resource
Required Follow up:
Cancer treatment plan established
Referral to Oncology
Within 6-12 months after treatment, a mammogram should be conducted to determine how to bring the patient back into surveillance













Sources
Follow ups mainly copied from https://www.cancercenter.com/cancer-types/breast-cancer/diagnosis-and-detection/mammography/results-bi-rads
Also added some based on email discussion to line up with scenarios

Asked ChatGPT the question below

Added more structure to document
Can you give me a description of the 6 bi-rad classifications, with the sub-classifications for 4 (A, B, C, D). I am looking for some criteria to check for in FHIR notes that can be used to determine a classification, such as, a lump of 0.4m with high density found within 2cm of the lymph nodes is class X
Absolutely—this is a very common need when you’re trying to infer BI-RADS from narrative imaging notes. I’ll do two things:
Give a clean, accurate description of BI-RADS 0–6, including 4A–4D


Translate each category into practical text/feature cues you might detect in FHIR DiagnosticReport / Observation / ImagingStudy notes, with important caveats about what cannot be reliably inferred


I’ll keep this grounded in how radiologists actually write.

BI-RADS overview (0–6)
BI-RADS 0 – Incomplete
Meaning
Imaging is insufficient to make a final assessment


Typical reasons
Need prior comparison


Need additional views (spot compression, magnification)


Need ultrasound or MRI correlation


FHIR / note cues
Phrases like:


“Additional imaging recommended”


“Comparison with prior studies needed”


“Incomplete evaluation”


“Recall for diagnostic mammography”


Orders for additional modality without a final assessment


Rule of thumb
If the report defers judgment → BI-RADS 0

BI-RADS 1 – Negative
Meaning
No findings of concern


Typical descriptors
Symmetric tissue


No masses, calcifications, or distortions


FHIR / note cues
“No suspicious mass, calcification, or architectural distortion”


“Negative mammogram”


“Unremarkable”


Rule of thumb
Explicitly normal → BI-RADS 1

BI-RADS 2 – Benign
Meaning
Findings are present, but clearly benign


Common benign findings
Simple cysts


Intramammary lymph nodes


Fat necrosis


Stable benign calcifications


Fibroadenomas (classic appearance)


FHIR / note cues
“Benign-appearing”


“Simple cyst”


“Fat-containing lesion”


“Involuting fibroadenoma”


“Stable for >2 years”


Rule of thumb
A finding is named, explained, and dismissed → BI-RADS 2

BI-RADS 3 – Probably Benign
Meaning
<2% likelihood of malignancy


Short-term follow-up recommended


Classic use cases
New but likely benign mass


Clustered punctate calcifications


Focal asymmetry without suspicious features


FHIR / note cues
“Probably benign”


“6-month follow-up recommended”


“Short-interval follow-up”


“Low suspicion”


Rule of thumb
Follow-up imaging instead of biopsy → BI-RADS 3

BI-RADS 4 – Suspicious
Biopsy should be considered
This is where your sub-classification logic matters most.
BI-RADS 4A – Low suspicion (≈2–10%)
Typical features
Small mass


Mostly circumscribed margins


Mildly suspicious calcifications


FHIR / note cues
“Low suspicion for malignancy”


“Biopsy recommended for confirmation”


“Indeterminate mass”


Circumscribed or partially obscured margins


Heuristic
Small lesion + mostly benign morphology + biopsy suggested
→ 4A

BI-RADS 4B – Moderate suspicion (≈10–50%)
Typical features
Irregular mass


Non-circumscribed margins


Heterogeneous density


New or enlarging lesion


FHIR / note cues
“Suspicious mass”


“Irregular shape”


“Indistinct margins”


“Moderate concern for malignancy”


Heuristic
Clearly abnormal morphology, but not classic cancer
→ 4B

BI-RADS 4C – High suspicion (≈50–95%)
Typical features
Spiculated margins


Marked architectural distortion


Pleomorphic or linear calcifications


Associated skin or nipple changes


FHIR / note cues
“Highly suspicious”


“Spiculated mass”


“Architectural distortion”


“Pleomorphic calcifications”


Heuristic
Looks like cancer, but not proven
→ 4C

BI-RADS 4D (sometimes called 4C+ or “near 5”)
Meaning
Some institutions use this informally


Essentially “almost BI-RADS 5”


FHIR / note cues
“Very high suspicion”


“Strongly concerning for malignancy”


Biopsy framed as urgent


Heuristic
Language nearly identical to BI-RADS 5 but stops short
→ 4D
⚠️ Important: 4D is not officially standardized everywhere, so treat it as optional metadata.

BI-RADS 5 – Highly Suggestive of Malignancy
Meaning
≥95% likelihood of cancer


Classic findings
Spiculated mass


Segmental linear calcifications


Skin thickening, nipple retraction


Pathologic lymph nodes


FHIR / note cues
“Highly suggestive of malignancy”


“Consistent with carcinoma”


“Urgent tissue diagnosis recommended”


Rule of thumb
Radiologist is convinced → BI-RADS 5

BI-RADS 6 – Known Malignancy
Meaning
Cancer already biopsy-proven


Imaging done for staging or treatment response


FHIR / note cues
“Known biopsy-proven malignancy”


“Status post core biopsy showing…”


Existing cancer diagnosis in Condition resource


Rule of thumb
Diagnosis known before imaging → BI-RADS 6

