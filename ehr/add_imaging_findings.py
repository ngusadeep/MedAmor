#!/usr/bin/env python3
"""Add imaging finding records to Richelle Wiegand's FHIR bundle.

Creates a test scenario for audit tool: mammography and ultrasound found
suspicious pathology (BI-RADS 4), biopsy was recommended but never performed.
"""

import json
import base64
import uuid

INPUT_FILE = "/home/claw/src/MedAudit/ehr/mod_Richelle340_Wiegand701_943fec3e-ac5a-2284-2b4f-ce652b6f09d3.json"

PATIENT_REF = "urn:uuid:943fec3e-ac5a-2284-2b4f-ce652b6f09d3"
ENCOUNTER_REF = "urn:uuid:943fec3e-ac5a-2284-62c0-c37f31e357a2"
DATETIME = "2026-01-30T23:27:24-07:00"
DATETIME_MS = "2026-01-30T23:27:24.000-07:00"
PRACTITIONER_REF = "Practitioner?identifier=http://hl7.org/fhir/sid/us-npi|9999970699"
PRACTITIONER_DISPLAY = "Dr. Ernest565 Runte676"


def make_uuid():
    return str(uuid.uuid4())


def entry_wrapper(resource):
    full_url = f"urn:uuid:{resource['id']}"
    return {
        "fullUrl": full_url,
        "resource": resource,
        "request": {
            "method": "POST",
            "url": resource["resourceType"]
        }
    }


def make_mammo_report():
    """DiagnosticReport for screening mammography findings."""
    narrative = """SCREENING MAMMOGRAPHY REPORT

Patient: Richelle340 Wiegand701
Date: 2026-01-30
Facility: Brigham & Women's Hospital

CLINICAL HISTORY:
49-year-old female presenting for routine screening mammography. No prior breast complaints. No family history of breast cancer documented.

TECHNIQUE:
Standard two-view digital mammography of bilateral breasts (CC and MLO views).

BREAST COMPOSITION:
Heterogeneously dense breast tissue (ACR Density Category C), which may obscure small masses.

FINDINGS:
Right breast: No suspicious masses, calcifications, or architectural distortion identified.

Left breast: A 1.2 cm irregular, spiculated mass is identified in the upper outer quadrant at approximately 10 o'clock position, 6 cm from the nipple. No associated calcifications. No skin thickening or retraction.

No suspicious axillary lymphadenopathy bilaterally.

IMPRESSION:
Left breast: 1.2 cm irregular spiculated mass, upper outer quadrant. Highly suspicious morphology.

BI-RADS ASSESSMENT: Category 4B - Moderate Suspicion for Malignancy

RECOMMENDATION:
Targeted diagnostic ultrasound of the left breast is recommended for further characterization. Tissue sampling (core needle biopsy) is strongly recommended regardless of ultrasound findings given the suspicious mammographic morphology.
"""
    rid = make_uuid()
    return entry_wrapper({
        "resourceType": "DiagnosticReport",
        "id": rid,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"]
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://loinc.org",
                "code": "24606-6",
                "display": "MG Breast Screening"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "24606-6",
                "display": "MG Breast Screening"
            }],
            "text": "MG Breast Screening"
        },
        "subject": {"reference": PATIENT_REF},
        "encounter": {"reference": ENCOUNTER_REF},
        "effectiveDateTime": DATETIME,
        "issued": DATETIME_MS,
        "performer": [{
            "reference": PRACTITIONER_REF,
            "display": PRACTITIONER_DISPLAY
        }],
        "conclusion": "BI-RADS 4B - Moderate Suspicion for Malignancy. 1.2 cm irregular spiculated mass, upper outer quadrant, left breast. Core needle biopsy strongly recommended.",
        "presentedForm": [{
            "contentType": "text/plain; charset=utf-8",
            "data": base64.b64encode(narrative.encode("utf-8")).decode("ascii")
        }]
    })


def make_birads_observation():
    """Observation for BI-RADS assessment category."""
    rid = make_uuid()
    return entry_wrapper({
        "resourceType": "Observation",
        "id": rid,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-clinical-result"]
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "imaging",
                "display": "Imaging"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "36625-2",
                "display": "Breast Imaging Reporting and Data System"
            }],
            "text": "Breast Imaging Reporting and Data System"
        },
        "subject": {"reference": PATIENT_REF},
        "encounter": {"reference": ENCOUNTER_REF},
        "effectiveDateTime": DATETIME,
        "issued": DATETIME_MS,
        "valueCodeableConcept": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "397183009",
                "display": "Mammography assessment (Category 4) (finding)"
            }],
            "text": "BI-RADS Category 4 - Suspicious Abnormality"
        }
    })


def make_mammo_mass_observation():
    """Observation for mammographic mass finding with components."""
    rid = make_uuid()
    return entry_wrapper({
        "resourceType": "Observation",
        "id": rid,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-clinical-result"]
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "imaging",
                "display": "Imaging"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "129748003",
                "display": "Mammographic mass (finding)"
            }],
            "text": "Mammographic mass (finding)"
        },
        "subject": {"reference": PATIENT_REF},
        "encounter": {"reference": ENCOUNTER_REF},
        "effectiveDateTime": DATETIME,
        "issued": DATETIME_MS,
        "valueCodeableConcept": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "129748003",
                "display": "Mammographic mass (finding)"
            }],
            "text": "Mammographic mass identified in left breast"
        },
        "bodySite": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "19100000",
                "display": "Structure of upper outer quadrant of left breast (body structure)"
            }],
            "text": "Upper outer quadrant of left breast"
        },
        "component": [
            {
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "272741003",
                        "display": "Laterality (attribute)"
                    }],
                    "text": "Laterality"
                },
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "7771000",
                        "display": "Left (qualifier value)"
                    }],
                    "text": "Left"
                }
            },
            {
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "33728-7",
                        "display": "Size.maximum dimension in Tumor"
                    }],
                    "text": "Tumor size"
                },
                "valueQuantity": {
                    "value": 1.2,
                    "unit": "cm",
                    "system": "http://unitsofmeasure.org",
                    "code": "cm"
                }
            },
            {
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "300842002",
                        "display": "Mass shape (attribute)"
                    }],
                    "text": "Shape"
                },
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "23085002",
                        "display": "Irregular (qualifier value)"
                    }],
                    "text": "Irregular"
                }
            },
            {
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "112233004",
                        "display": "Mass margin (attribute)"
                    }],
                    "text": "Margin"
                },
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "81711004",
                        "display": "Spiculated (qualifier value)"
                    }],
                    "text": "Spiculated"
                }
            }
        ]
    })


def make_us_report():
    """DiagnosticReport for breast ultrasound findings."""
    narrative = """TARGETED BREAST ULTRASOUND REPORT

Patient: Richelle340 Wiegand701
Date: 2026-01-30
Facility: Brigham & Women's Hospital

CLINICAL INDICATION:
Targeted ultrasound evaluation of mammographically detected 1.2 cm irregular mass in the left breast upper outer quadrant.

TECHNIQUE:
Real-time ultrasound evaluation of the left breast with high-frequency linear transducer.

FINDINGS:
Left breast, 10 o'clock position, 6 cm from nipple:
A 1.3 x 1.0 x 0.9 cm solid, hypoechoic mass is identified correlating with the mammographic finding. The mass demonstrates:
- Irregular shape
- Non-parallel orientation (taller than wide)
- Indistinct/angular margins
- Marked hypoechogenicity
- Posterior acoustic shadowing
- No internal vascularity on color Doppler

No additional suspicious masses or lesions identified in the left breast.

Left axilla: Two mildly prominent lymph nodes identified measuring up to 1.5 cm in short axis. The cortex appears mildly thickened but fatty hilum is preserved. Findings are indeterminate.

IMPRESSION:
1.3 cm solid hypoechoic mass at left breast 10 o'clock, correlating with mammographic finding. Multiple suspicious sonographic features (irregular shape, angular margins, shadowing, non-parallel orientation).

BI-RADS ASSESSMENT: Category 4B - Moderate Suspicion for Malignancy (concordant with mammographic assessment)

RECOMMENDATION:
Ultrasound-guided core needle biopsy is strongly recommended. Left axillary lymph node sampling should be considered at the time of biopsy.
"""
    rid = make_uuid()
    return entry_wrapper({
        "resourceType": "DiagnosticReport",
        "id": rid,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"]
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://loinc.org",
                "code": "24590-2",
                "display": "US Breast"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "24590-2",
                "display": "US Breast"
            }],
            "text": "US Breast"
        },
        "subject": {"reference": PATIENT_REF},
        "encounter": {"reference": ENCOUNTER_REF},
        "effectiveDateTime": DATETIME,
        "issued": DATETIME_MS,
        "performer": [{
            "reference": PRACTITIONER_REF,
            "display": PRACTITIONER_DISPLAY
        }],
        "conclusion": "BI-RADS 4B - Moderate Suspicion for Malignancy. 1.3 cm hypoechoic solid mass with irregular margins and posterior shadowing, left breast 10 o'clock. Ultrasound-guided core needle biopsy strongly recommended.",
        "presentedForm": [{
            "contentType": "text/plain; charset=utf-8",
            "data": base64.b64encode(narrative.encode("utf-8")).decode("ascii")
        }]
    })


def make_us_mass_observation():
    """Observation for ultrasound mass finding with components."""
    rid = make_uuid()
    return entry_wrapper({
        "resourceType": "Observation",
        "id": rid,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-clinical-result"]
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "imaging",
                "display": "Imaging"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "390790000",
                "display": "Ultrasound scan of breast (procedure)"
            }],
            "text": "Breast ultrasound finding"
        },
        "subject": {"reference": PATIENT_REF},
        "encounter": {"reference": ENCOUNTER_REF},
        "effectiveDateTime": DATETIME,
        "issued": DATETIME_MS,
        "valueCodeableConcept": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "129766003",
                "display": "Hypoechoic mass of breast (finding)"
            }],
            "text": "Hypoechoic solid mass, left breast"
        },
        "bodySite": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "19100000",
                "display": "Structure of upper outer quadrant of left breast (body structure)"
            }],
            "text": "Left breast, 10 o'clock, 6 cm from nipple"
        },
        "component": [
            {
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "33728-7",
                        "display": "Size.maximum dimension in Tumor"
                    }],
                    "text": "Mass size"
                },
                "valueQuantity": {
                    "value": 1.3,
                    "unit": "cm",
                    "system": "http://unitsofmeasure.org",
                    "code": "cm"
                }
            },
            {
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "300842002",
                        "display": "Mass shape (attribute)"
                    }],
                    "text": "Shape"
                },
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "23085002",
                        "display": "Irregular (qualifier value)"
                    }],
                    "text": "Irregular"
                }
            },
            {
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "112233004",
                        "display": "Mass margin (attribute)"
                    }],
                    "text": "Margin"
                },
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "129742005",
                        "display": "Indistinct (qualifier value)"
                    }],
                    "text": "Indistinct/angular"
                }
            },
            {
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "118420003",
                        "display": "Echogenicity (attribute)"
                    }],
                    "text": "Echogenicity"
                },
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "65943003",
                        "display": "Hypoechoic (qualifier value)"
                    }],
                    "text": "Markedly hypoechoic"
                }
            },
            {
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "118421004",
                        "display": "Posterior acoustic features (attribute)"
                    }],
                    "text": "Posterior acoustic features"
                },
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "31781000",
                        "display": "Acoustic shadowing (finding)"
                    }],
                    "text": "Posterior acoustic shadowing"
                }
            },
            {
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "250142004",
                        "display": "Orientation of mass (attribute)"
                    }],
                    "text": "Orientation"
                },
                "valueCodeableConcept": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "250143009",
                        "display": "Not parallel (qualifier value)"
                    }],
                    "text": "Not parallel (taller than wide)"
                }
            }
        ]
    })


def make_clinical_note():
    """DiagnosticReport with updated H&P reflecting imaging findings and biopsy recommendation."""
    narrative = """2026-01-30

# Chief Complaint
No complaints. Patient presents for routine breast cancer screening.

# History of Present Illness
Richelle340 is a 49 year-old nonhispanic white female presenting for periodic health evaluation including breast cancer screening mammography.

# Social History
Patient is married. Patient has never smoked.
Patient identifies as heterosexual.

Patient comes from a middle socioeconomic background.
Patient has a high school education.
Patient currently has Humana.

# Allergies
No Known Allergies.

# Medications
No Active Medications.

# Assessment and Plan

## Imaging Results

### Screening Mammography
Heterogeneously dense breast tissue (ACR Density C). A 1.2 cm irregular, spiculated mass was identified in the upper outer quadrant of the left breast at approximately 10 o'clock position.
BI-RADS Assessment: Category 4B - Moderate Suspicion for Malignancy.

### Targeted Breast Ultrasound
Correlating 1.3 cm solid hypoechoic mass at left breast 10 o'clock. Multiple suspicious sonographic features: irregular shape, non-parallel orientation, angular margins, marked hypoechogenicity, posterior acoustic shadowing.
BI-RADS Assessment: Category 4B (concordant).

Mildly prominent left axillary lymph nodes with preserved fatty hilum. Indeterminate significance.

## Assessment
Suspicious breast mass, left breast. BI-RADS 4B on both mammography and ultrasound.

## Plan
- Ultrasound-guided core needle biopsy of the left breast mass is strongly recommended
- Consider left axillary lymph node sampling at time of biopsy
- Results to be discussed at follow-up appointment
- Patient counseled regarding findings and recommendations
"""
    rid = make_uuid()
    return entry_wrapper({
        "resourceType": "DiagnosticReport",
        "id": rid,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"]
        },
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://loinc.org",
                "code": "34117-2",
                "display": "History and physical note"
            }, {
                "system": "http://loinc.org",
                "code": "51847-2",
                "display": "Evaluation + Plan note"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "34117-2",
                "display": "History and physical note"
            }, {
                "system": "http://loinc.org",
                "code": "51847-2",
                "display": "Evaluation + Plan note"
            }]
        },
        "subject": {"reference": PATIENT_REF},
        "encounter": {"reference": ENCOUNTER_REF},
        "effectiveDateTime": DATETIME,
        "issued": DATETIME_MS,
        "performer": [{
            "reference": PRACTITIONER_REF,
            "display": PRACTITIONER_DISPLAY
        }],
        "presentedForm": [{
            "contentType": "text/plain; charset=utf-8",
            "data": base64.b64encode(narrative.encode("utf-8")).decode("ascii")
        }]
    })


def main():
    with open(INPUT_FILE) as f:
        bundle = json.load(f)

    print(f"Original entry count: {len(bundle['entry'])}")

    new_entries = [
        make_mammo_report(),
        make_birads_observation(),
        make_mammo_mass_observation(),
        make_us_report(),
        make_us_mass_observation(),
        make_clinical_note(),
    ]

    # Insert after entry 36 (ultrasound procedure, the last current entry)
    bundle["entry"].extend(new_entries)
    print(f"Added {len(new_entries)} imaging finding entries")
    print(f"New entry count: {len(bundle['entry'])}")

    with open(INPUT_FILE, "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"Wrote to {INPUT_FILE}")

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
        print(f"  [{i}] {rtype:25s} | {code}")


if __name__ == "__main__":
    main()
