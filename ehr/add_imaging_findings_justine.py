#!/usr/bin/env python3
"""Strip Justine Schoen's FHIR bundle to imaging-only, then add imaging findings.

Creates a test scenario for audit tool: mammography and ultrasound found
suspicious pathology (BI-RADS 4), biopsy was recommended but never performed.

Steps:
1. Keep entries 0-34 (patient history + screening encounter)
2. Keep mammography (entry 49) and ultrasound (entry 50) procedures
3. Remove everything else (condition, observations, biopsy, treatment, follow-ups)
4. Trim encounter end date to match imaging-only timeframe
5. Add imaging finding records (mammo report, BI-RADS, US report, mass findings, clinical note)
"""

import json
import base64
import uuid

INPUT_FILE = "/home/claw/src/MedAudit/ehr/mod_Justine412_Garnett735_Schoen8_39b7de4b-abf2-d772-461e-193e503a035b.json"

PATIENT_REF = "urn:uuid:39b7de4b-abf2-d772-461e-193e503a035b"
ENCOUNTER_REF = "urn:uuid:39b7de4b-abf2-d772-5632-7f8a2797109c"
DATETIME = "2023-07-23T06:52:48-08:00"  # after ultrasound end
DATETIME_MS = "2023-07-23T06:52:48.000-08:00"
PRACTITIONER_REF = "Practitioner?identifier=http://hl7.org/fhir/sid/us-npi|9999998294"
PRACTITIONER_DISPLAY = "Dr. Bennett146 Rippin620"
LOCATION = "MILFORD REGIONAL MEDICAL CENTER"

MAMMO_UUID = "urn:uuid:39b7de4b-abf2-d772-d052-1277136e8515"
US_UUID = "urn:uuid:39b7de4b-abf2-d772-8954-820b384e2cfb"


def make_uuid():
    return str(uuid.uuid4())


def entry_wrapper(resource):
    full_url = f"urn:uuid:{resource['id']}"
    return {
        "fullUrl": full_url,
        "resource": resource,
        "request": {"method": "POST", "url": resource["resourceType"]},
    }


def make_mammo_report():
    narrative = """SCREENING MAMMOGRAPHY REPORT

Patient: Justine412 Schoen8
Date: 2023-07-23
Facility: Milford Regional Medical Center

CLINICAL HISTORY:
44-year-old female presenting for routine screening mammography. No prior breast complaints. No palpable masses. No nipple discharge.

TECHNIQUE:
Standard two-view digital mammography of bilateral breasts (CC and MLO views).

BREAST COMPOSITION:
Heterogeneously dense breast tissue (ACR Density Category C), which may obscure small masses.

FINDINGS:
Right breast: No suspicious masses, calcifications, or architectural distortion identified.

Left breast: A 1.4 cm irregular mass with indistinct margins is identified in the upper outer quadrant at approximately 2 o'clock position, 5 cm from the nipple. Associated fine pleomorphic microcalcifications are noted within and adjacent to the mass. No skin thickening or retraction. No architectural distortion.

No suspicious axillary lymphadenopathy bilaterally.

IMPRESSION:
Left breast: 1.4 cm irregular mass with associated pleomorphic microcalcifications, upper outer quadrant. Morphology is highly suspicious.

BI-RADS ASSESSMENT: Category 4C - High Suspicion for Malignancy

RECOMMENDATION:
Targeted diagnostic ultrasound of the left breast is recommended for further characterization. Tissue sampling (core needle biopsy) is strongly recommended. Stereotactic biopsy of the calcifications should also be considered.
"""
    rid = make_uuid()
    return entry_wrapper(
        {
            "resourceType": "DiagnosticReport",
            "id": rid,
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"
                ]
            },
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "24606-6",
                            "display": "MG Breast Screening",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "24606-6",
                        "display": "MG Breast Screening",
                    }
                ],
                "text": "MG Breast Screening",
            },
            "subject": {"reference": PATIENT_REF},
            "encounter": {"reference": ENCOUNTER_REF},
            "effectiveDateTime": DATETIME,
            "issued": DATETIME_MS,
            "performer": [
                {"reference": PRACTITIONER_REF, "display": PRACTITIONER_DISPLAY}
            ],
            "conclusion": "BI-RADS 4C - High Suspicion for Malignancy. 1.4 cm irregular mass with associated pleomorphic microcalcifications, upper outer quadrant, left breast. Core needle biopsy strongly recommended.",
            "presentedForm": [
                {
                    "contentType": "text/plain; charset=utf-8",
                    "data": base64.b64encode(narrative.encode("utf-8")).decode("ascii"),
                }
            ],
        }
    )


def make_birads_observation():
    rid = make_uuid()
    return entry_wrapper(
        {
            "resourceType": "Observation",
            "id": rid,
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-clinical-result"
                ]
            },
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "imaging",
                            "display": "Imaging",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "36625-2",
                        "display": "Breast Imaging Reporting and Data System",
                    }
                ],
                "text": "Breast Imaging Reporting and Data System",
            },
            "subject": {"reference": PATIENT_REF},
            "encounter": {"reference": ENCOUNTER_REF},
            "effectiveDateTime": DATETIME,
            "issued": DATETIME_MS,
            "valueCodeableConcept": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "397183009",
                        "display": "Mammography assessment (Category 4) (finding)",
                    }
                ],
                "text": "BI-RADS Category 4C - High Suspicion for Malignancy",
            },
        }
    )


def make_mammo_mass_observation():
    rid = make_uuid()
    return entry_wrapper(
        {
            "resourceType": "Observation",
            "id": rid,
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-clinical-result"
                ]
            },
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "imaging",
                            "display": "Imaging",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "129748003",
                        "display": "Mammographic mass (finding)",
                    }
                ],
                "text": "Mammographic mass (finding)",
            },
            "subject": {"reference": PATIENT_REF},
            "encounter": {"reference": ENCOUNTER_REF},
            "effectiveDateTime": DATETIME,
            "issued": DATETIME_MS,
            "valueCodeableConcept": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "129748003",
                        "display": "Mammographic mass (finding)",
                    }
                ],
                "text": "Mammographic mass with associated microcalcifications, left breast",
            },
            "bodySite": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "19100000",
                        "display": "Structure of upper outer quadrant of left breast (body structure)",
                    }
                ],
                "text": "Upper outer quadrant of left breast",
            },
            "component": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "272741003",
                                "display": "Laterality (attribute)",
                            }
                        ],
                        "text": "Laterality",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "7771000",
                                "display": "Left (qualifier value)",
                            }
                        ],
                        "text": "Left",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "33728-7",
                                "display": "Size.maximum dimension in Tumor",
                            }
                        ],
                        "text": "Tumor size",
                    },
                    "valueQuantity": {
                        "value": 1.4,
                        "unit": "cm",
                        "system": "http://unitsofmeasure.org",
                        "code": "cm",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "300842002",
                                "display": "Mass shape (attribute)",
                            }
                        ],
                        "text": "Shape",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "23085002",
                                "display": "Irregular (qualifier value)",
                            }
                        ],
                        "text": "Irregular",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "112233004",
                                "display": "Mass margin (attribute)",
                            }
                        ],
                        "text": "Margin",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "129742005",
                                "display": "Indistinct (qualifier value)",
                            }
                        ],
                        "text": "Indistinct",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "129770003",
                                "display": "Calcification morphology (attribute)",
                            }
                        ],
                        "text": "Associated calcifications",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "129764000",
                                "display": "Fine pleomorphic microcalcifications (finding)",
                            }
                        ],
                        "text": "Fine pleomorphic microcalcifications",
                    },
                },
            ],
        }
    )


def make_us_report():
    narrative = """TARGETED BREAST ULTRASOUND REPORT

Patient: Justine412 Schoen8
Date: 2023-07-23
Facility: Milford Regional Medical Center

CLINICAL INDICATION:
Targeted ultrasound evaluation of mammographically detected 1.4 cm irregular mass with associated microcalcifications in the left breast upper outer quadrant.

TECHNIQUE:
Real-time ultrasound evaluation of the left breast with high-frequency linear transducer.

FINDINGS:
Left breast, 2 o'clock position, 5 cm from nipple:
A 1.5 x 1.1 x 1.0 cm solid, hypoechoic mass is identified correlating with the mammographic finding. The mass demonstrates:
- Irregular shape
- Non-parallel orientation (taller than wide)
- Angular and microlobulated margins
- Marked hypoechogenicity
- Posterior acoustic shadowing
- Increased peripheral vascularity on color Doppler
- Small echogenic foci within the mass, likely corresponding to the mammographic calcifications

No additional suspicious masses or lesions identified in either breast.

Left axilla: A single morphologically suspicious lymph node measuring 1.8 cm in short axis is identified. The cortex is eccentrically thickened (6 mm) with partial effacement of the fatty hilum. This is concerning for metastatic involvement.

Right axilla: Normal-appearing lymph nodes.

IMPRESSION:
1. 1.5 cm solid hypoechoic mass at left breast 2 o'clock, correlating with mammographic finding. Multiple suspicious sonographic features including irregular shape, angular margins, shadowing, non-parallel orientation, and increased vascularity. Internal echogenic foci corresponding to calcifications.

2. Morphologically suspicious left axillary lymph node with eccentric cortical thickening.

BI-RADS ASSESSMENT: Category 4C - High Suspicion for Malignancy (concordant with mammographic assessment)

RECOMMENDATION:
Ultrasound-guided core needle biopsy of the left breast mass is strongly recommended. Ultrasound-guided fine needle aspiration or core biopsy of the suspicious left axillary lymph node should be performed at the same time.
"""
    rid = make_uuid()
    return entry_wrapper(
        {
            "resourceType": "DiagnosticReport",
            "id": rid,
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"
                ]
            },
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "24590-2",
                            "display": "US Breast",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "24590-2",
                        "display": "US Breast",
                    }
                ],
                "text": "US Breast",
            },
            "subject": {"reference": PATIENT_REF},
            "encounter": {"reference": ENCOUNTER_REF},
            "effectiveDateTime": DATETIME,
            "issued": DATETIME_MS,
            "performer": [
                {"reference": PRACTITIONER_REF, "display": PRACTITIONER_DISPLAY}
            ],
            "conclusion": "BI-RADS 4C - High Suspicion for Malignancy. 1.5 cm hypoechoic solid mass with irregular margins, posterior shadowing, and increased vascularity, left breast 2 o'clock. Suspicious left axillary lymph node. Ultrasound-guided core needle biopsy strongly recommended for both lesions.",
            "presentedForm": [
                {
                    "contentType": "text/plain; charset=utf-8",
                    "data": base64.b64encode(narrative.encode("utf-8")).decode("ascii"),
                }
            ],
        }
    )


def make_us_mass_observation():
    rid = make_uuid()
    return entry_wrapper(
        {
            "resourceType": "Observation",
            "id": rid,
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-clinical-result"
                ]
            },
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "imaging",
                            "display": "Imaging",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "390790000",
                        "display": "Ultrasound scan of breast (procedure)",
                    }
                ],
                "text": "Breast ultrasound finding",
            },
            "subject": {"reference": PATIENT_REF},
            "encounter": {"reference": ENCOUNTER_REF},
            "effectiveDateTime": DATETIME,
            "issued": DATETIME_MS,
            "valueCodeableConcept": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "129766003",
                        "display": "Hypoechoic mass of breast (finding)",
                    }
                ],
                "text": "Hypoechoic solid mass with internal calcifications, left breast",
            },
            "bodySite": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "19100000",
                        "display": "Structure of upper outer quadrant of left breast (body structure)",
                    }
                ],
                "text": "Left breast, 2 o'clock, 5 cm from nipple",
            },
            "component": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "33728-7",
                                "display": "Size.maximum dimension in Tumor",
                            }
                        ],
                        "text": "Mass size",
                    },
                    "valueQuantity": {
                        "value": 1.5,
                        "unit": "cm",
                        "system": "http://unitsofmeasure.org",
                        "code": "cm",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "300842002",
                                "display": "Mass shape (attribute)",
                            }
                        ],
                        "text": "Shape",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "23085002",
                                "display": "Irregular (qualifier value)",
                            }
                        ],
                        "text": "Irregular",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "112233004",
                                "display": "Mass margin (attribute)",
                            }
                        ],
                        "text": "Margin",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "129743000",
                                "display": "Angular (qualifier value)",
                            }
                        ],
                        "text": "Angular and microlobulated",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "118420003",
                                "display": "Echogenicity (attribute)",
                            }
                        ],
                        "text": "Echogenicity",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "65943003",
                                "display": "Hypoechoic (qualifier value)",
                            }
                        ],
                        "text": "Markedly hypoechoic",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "118421004",
                                "display": "Posterior acoustic features (attribute)",
                            }
                        ],
                        "text": "Posterior acoustic features",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "31781000",
                                "display": "Acoustic shadowing (finding)",
                            }
                        ],
                        "text": "Posterior acoustic shadowing",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "250142004",
                                "display": "Orientation of mass (attribute)",
                            }
                        ],
                        "text": "Orientation",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "250143009",
                                "display": "Not parallel (qualifier value)",
                            }
                        ],
                        "text": "Not parallel (taller than wide)",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "129777006",
                                "display": "Vascularity of mass (attribute)",
                            }
                        ],
                        "text": "Vascularity",
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "129778001",
                                "display": "Increased vascularity (finding)",
                            }
                        ],
                        "text": "Increased peripheral vascularity",
                    },
                },
            ],
        }
    )


def make_clinical_note():
    narrative = """2023-07-23

# Chief Complaint
No complaints. Patient presents for routine breast cancer screening.

# History of Present Illness
Justine412 is a 44 year-old nonhispanic pacific islander female presenting for periodic health evaluation including breast cancer screening mammography.

# Social History
Patient is married. Patient has never smoked.
Patient identifies as heterosexual.

Patient comes from a middle socioeconomic background.
Patient has a high school education.
Patient currently has Aetna.

# Allergies
No Known Allergies.

# Medications
No Active Medications.

# Assessment and Plan

## Imaging Results

### Screening Mammography
Heterogeneously dense breast tissue (ACR Density C). A 1.4 cm irregular mass with indistinct margins and associated fine pleomorphic microcalcifications was identified in the upper outer quadrant of the left breast at approximately 2 o'clock position.
BI-RADS Assessment: Category 4C - High Suspicion for Malignancy.

### Targeted Breast Ultrasound
Correlating 1.5 cm solid hypoechoic mass at left breast 2 o'clock. Multiple suspicious sonographic features: irregular shape, non-parallel orientation, angular margins, marked hypoechogenicity, posterior acoustic shadowing, increased peripheral vascularity. Internal echogenic foci corresponding to mammographic calcifications.

Morphologically suspicious left axillary lymph node with eccentric cortical thickening (6 mm) and partial hilum effacement.

BI-RADS Assessment: Category 4C (concordant).

## Assessment
Highly suspicious breast mass, left breast. BI-RADS 4C on both mammography and ultrasound. Suspicious left axillary lymphadenopathy.

## Plan
- Ultrasound-guided core needle biopsy of the left breast mass is strongly recommended
- Ultrasound-guided FNA or core biopsy of the suspicious left axillary lymph node at the same session
- Stereotactic biopsy of the associated calcifications should be considered
- Results to be discussed at multidisciplinary tumor board
- Patient counseled regarding findings and recommendations
"""
    rid = make_uuid()
    return entry_wrapper(
        {
            "resourceType": "DiagnosticReport",
            "id": rid,
            "meta": {
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"
                ]
            },
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "34117-2",
                            "display": "History and physical note",
                        },
                        {
                            "system": "http://loinc.org",
                            "code": "51847-2",
                            "display": "Evaluation + Plan note",
                        },
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "34117-2",
                        "display": "History and physical note",
                    },
                    {
                        "system": "http://loinc.org",
                        "code": "51847-2",
                        "display": "Evaluation + Plan note",
                    },
                ]
            },
            "subject": {"reference": PATIENT_REF},
            "encounter": {"reference": ENCOUNTER_REF},
            "effectiveDateTime": DATETIME,
            "issued": DATETIME_MS,
            "performer": [
                {"reference": PRACTITIONER_REF, "display": PRACTITIONER_DISPLAY}
            ],
            "presentedForm": [
                {
                    "contentType": "text/plain; charset=utf-8",
                    "data": base64.b64encode(narrative.encode("utf-8")).decode("ascii"),
                }
            ],
        }
    )


def main():
    with open(INPUT_FILE) as f:
        bundle = json.load(f)

    original_count = len(bundle["entry"])
    print(f"Original entry count: {original_count}")

    # Step 1: Keep entries 0-34, plus mammography and ultrasound procedures
    kept = bundle["entry"][:35]  # entries 0-34

    # Extract imaging procedures from their original positions
    imaging_entries = []
    for entry in bundle["entry"][35:]:
        if entry.get("fullUrl") in (MAMMO_UUID, US_UUID):
            imaging_entries.append(entry)
            code = entry["resource"]["code"]["coding"][0]["display"]
            print(f"  Preserving: {code}")

    kept.extend(imaging_entries)
    removed = original_count - len(kept)
    bundle["entry"] = kept
    print(f"Step 1: Removed {removed} entries (kept {len(kept)})")

    # Step 2: Trim encounter end date to match imaging timeframe
    enc = bundle["entry"][34]["resource"]
    old_end = enc["period"]["end"]
    # Set end to ultrasound end time
    enc["period"]["end"] = "2023-07-23T06:52:48-08:00"
    print(f"Step 2: Trimmed encounter end: {old_end} -> {enc['period']['end']}")

    # Step 3: Add imaging finding records
    new_entries = [
        make_mammo_report(),
        make_birads_observation(),
        make_mammo_mass_observation(),
        make_us_report(),
        make_us_mass_observation(),
        make_clinical_note(),
    ]
    bundle["entry"].extend(new_entries)
    print(f"Step 3: Added {len(new_entries)} imaging finding entries")
    print(f"Final entry count: {len(bundle['entry'])}")

    # Write output
    with open(INPUT_FILE, "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"\nWrote to {INPUT_FILE}")

    # Verification
    print("\n--- Verification ---")
    with open(INPUT_FILE) as f:
        result = json.load(f)
    print(f"Valid JSON: Yes")
    print(f"Entry count: {len(result['entry'])}")

    # Check for BI-RADS
    for entry in result["entry"]:
        res = entry.get("resource", {})
        code = res.get("code", {}).get("coding", [{}])[0].get("display", "")
        if "Breast Imaging Reporting" in code:
            val = res.get("valueCodeableConcept", {}).get("text", "")
            print(f"BI-RADS observation: {val}")

    # Check for biopsy recommendation in reports
    for entry in result["entry"]:
        res = entry.get("resource", {})
        conclusion = res.get("conclusion", "")
        if "biopsy" in conclusion.lower():
            code = res.get("code", {}).get("coding", [{}])[0].get("display", "")
            print(f"Biopsy recommended in: {code}")

    # Confirm no biopsy procedure
    has_biopsy = False
    for entry in result["entry"]:
        res = entry.get("resource", {})
        if res.get("resourceType") == "Procedure":
            code = res.get("code", {}).get("coding", [{}])[0].get("display", "")
            if "biopsy" in code.lower():
                has_biopsy = True
    print(f"Biopsy procedure exists: {has_biopsy}")

    # Confirm no cancer diagnosis
    has_condition = False
    for entry in result["entry"]:
        res = entry.get("resource", {})
        if res.get("resourceType") == "Condition":
            has_condition = True
    print(f"Cancer condition exists: {has_condition}")

    # Print final entry list
    print("\nFinal entries:")
    for i, entry in enumerate(result["entry"]):
        res = entry.get("resource", {})
        rtype = res.get("resourceType", "?")
        code = ""
        if "code" in res:
            codings = res["code"].get("coding", [])
            if codings:
                code = codings[0].get("display", "")
        if not code and "type" in res and isinstance(res["type"], list):
            for t in res["type"]:
                codings = t.get("coding", [])
                if codings:
                    code = codings[0].get("display", "")
                    break
        start = res.get("period", res.get("performedPeriod", {})).get("start", "")[:10]
        if not start:
            start = res.get(
                "effectiveDateTime", res.get("onsetDateTime", res.get("date", ""))
            )[:10]
        print(f"  [{i}] {start:12s} | {rtype:25s} | {code}")


if __name__ == "__main__":
    main()
