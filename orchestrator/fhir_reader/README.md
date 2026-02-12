# FHIR Timeline Converter

A Python library that converts FHIR Bundle resources into chronological, narrative timelines optimized for LLM review and consistency checking.

## Overview

This library takes complex FHIR (Fast Healthcare Interoperability Resources) data and presents it in a simple, time-ordered narrative format. This makes it much easier for both humans and Large Language Models (LLMs) to:

- Review patient medical histories for consistency
- Identify timeline inconsistencies
- Spot potential medication conflicts
- Detect missing follow-ups
- Understand the complete patient journey

## Features

- **Chronological ordering**: All events sorted by datetime, not by resource type
- **Simple narrative format**: Easy-to-read text instead of nested JSON
- **Comprehensive**: Handles encounters, medications, allergies, conditions, procedures, observations, immunizations, care plans, and more
- **Configurable**: Choose what information to include (costs, medical codes, etc.)
- **Statistics**: Get summary stats about the patient record
- **LLM-optimized**: Perfect format for feeding to AI models for analysis

## Installation

```bash
pip install requests  # Only dependency
```

## Quick Start

```python
from aibroker.fhir_reader import load_and_convert

# Convert a FHIR bundle file to timeline
timeline = load_and_convert('patient_bundle.json')
print(timeline)
```

## Usage Examples

### Example 1: Basic File Conversion

```python
from aibroker.fhir_reader import load_and_convert

timeline = load_and_convert('patient_data.json')
print(timeline)
```

### Example 2: From FHIR API Response

```python
import requests
from aibroker.fhir_reader import convert_fhir_bundle_to_timeline

# Fetch from FHIR server
response = requests.get('http://fhir-server/Patient/123/$everything')
bundle = response.json()

# Convert to timeline
timeline = convert_fhir_bundle_to_timeline(bundle)
print(timeline)
```

### Example 3: Advanced Usage with Statistics

```python
from aibroker.fhir_reader import FHIRTimelineConverter
import json

with open('patient_data.json', 'r') as f:
    bundle = json.load(f)

converter = FHIRTimelineConverter(bundle)

# Get statistics first
stats = converter.get_summary_stats()
print(f"Total events: {stats['total_events']}")
print(f"Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")
print(f"Encounters: {stats['encounters']}")
print(f"Medications: {stats['medications']}")

# Convert to timeline
timeline = converter.convert(include_costs=False)
print(timeline)
```

### Example 4: LLM Consistency Checking

```python
from aibroker.fhir_reader import load_and_convert

timeline = load_and_convert('patient_data.json')

# Send to LLM for consistency checking
prompt = f"""
Review this patient medical timeline and identify any inconsistencies:

{timeline}

Check for:
1. Treatments prescribed before diagnosis
2. Medication conflicts with known allergies
3. Age-inappropriate medications
4. Missing follow-ups for serious conditions
5. Timeline logic issues
"""

# Send prompt to your LLM of choice...
```

## Output Format

The library generates a narrative timeline like this:

```
================================================================================
PATIENT MEDICAL TIMELINE
================================================================================

PATIENT INFORMATION:
  Name: Mrs. Reva678 Barrows492
  Patient ID: 26171
  Date of Birth: 1982-10-10
  Gender: Female
  Race: White
  Ethnicity: Not Hispanic or Latino

CHRONOLOGICAL TIMELINE:
--------------------------------------------------------------------------------

📅 1983-04-25

  [11:12:35] VISIT: Encounter for problem (procedure)
    Reason: Glycine max (substance)
    Provider: Dr. Clifton91 Lakin515
    Duration: 11:12:35 - 11:27:35

📅 1983-05-15

  [03:12:35] ALLERGY RECORDED: Mold (organism)
    Type: allergy, Category: environment
    Criticality: low
    Reactions: Sneezing (finding)

  [03:52:23] MEDICATION PRESCRIBED: diphenhydrAMINE Hydrochloride 25 MG Oral Tablet
    Status: active
    Dosage: Take as needed.
    Prescribed by: Dr. Clifton91 Lakin515
```

## Supported FHIR Resources

The library extracts timeline events from **32 FHIR resource types**, covering all resources needed for imaging workflows and handoff scenarios.

### Core Clinical Resources
- **Patient** - Demographics and basic information
- **Encounter** - Visits, appointments, hospitalizations
- **Condition** - Diagnoses, problems, health conditions
- **AllergyIntolerance** - Allergies and intolerances with reactions
- **Observation** - Lab results, vital signs, assessments, measurements
- **Procedure** - Surgical and medical procedures
- **FamilyMemberHistory** - Family medical history
- **ClinicalImpression** - Clinical assessments and impressions

### Imaging & Diagnostics
- **ImagingStudy** - Radiology studies (CT, MRI, X-ray, etc.)
- **DiagnosticReport** - Diagnostic test results, radiology reports, pathology
- **ServiceRequest** - Orders for tests, procedures, referrals

### Medication Resources
- **MedicationRequest** - Medication prescriptions and orders
- **MedicationAdministration** - Actual medication given to patient
- **MedicationStatement** - Patient-reported or historical medications

### Care Coordination
- **CarePlan** - Care plans and treatment protocols
- **Goal** - Treatment goals and objectives
- **EpisodeOfCare** - Care episodes and care context

### Communication & Tasks
- **Task** - Clinical and administrative tasks
- **Communication** - Communications between parties
- **CommunicationRequest** - Requested communications
- **Flag** - Clinical alerts and warnings

### Administrative & Workflow
- **Appointment** - Scheduled appointments
- **DocumentReference** - Clinical documents, notes, images
- **Claim** - Insurance claims with cost information

### Devices & Immunizations
- **DeviceUseStatement** - Medical device usage
- **Immunization** - Vaccines administered

### Audit & Provenance
- **Provenance** - Data provenance and attribution
- **AuditEvent** - System audit events

### Reference Resources (no timeline events)
- **Practitioner** - Healthcare providers (referenced)
- **PractitionerRole** - Provider roles (referenced)
- **Organization** - Healthcare organizations (referenced)
- **Location** - Physical locations (referenced)

**Total: 32 resource types supported**

## API Reference

### `load_and_convert(filepath, include_costs=True, include_codes=False)`

Load a FHIR bundle from a JSON file and convert to timeline.

**Parameters:**
- `filepath` (str): Path to JSON file containing FHIR Bundle
- `include_costs` (bool): Include cost information from claims (default: True)
- `include_codes` (bool): Include medical codes like SNOMED, LOINC (default: False)

**Returns:** Formatted timeline string

### `convert_fhir_bundle_to_timeline(bundle_json, include_costs=True, include_codes=False)`

Convert a FHIR bundle to timeline format.

**Parameters:**
- `bundle_json` (str or dict): FHIR Bundle as JSON string or dictionary
- `include_costs` (bool): Include cost information (default: True)
- `include_codes` (bool): Include medical codes (default: False)

**Returns:** Formatted timeline string

### `FHIRTimelineConverter` Class

Main converter class for more control.

**Methods:**

- `__init__(bundle)`: Initialize with FHIR Bundle dictionary
- `convert(include_costs=True, include_codes=False)`: Convert to timeline string
- `get_summary_stats()`: Get statistics about the patient record

**Statistics returned:**
```python
{
    'total_events': 15,
    'event_types': {'encounter': 3, 'medication': 2, ...},
    'date_range': {
        'start': '1983-04-25',
        'end': '2000-12-03',
        'span_days': 6431
    },
    'encounters': 3,
    'medications': 2,
    'allergies': 1,
    'conditions': 0,
    'procedures': 0
}
```

## Use Cases

### Medical Record Review
Convert patient records into chronological narratives for easier review by healthcare providers.

### AI-Powered Consistency Checking
Feed timelines to LLMs to detect:
- Medication conflicts with allergies
- Missing follow-up appointments
- Treatments before diagnoses
- Age-inappropriate medications
- Duplicate or contradictory information

### Research and Analytics
Generate readable summaries of patient journeys for research analysis.

### Clinical Decision Support
Present complete patient history in chronological order for clinical decision-making.

### Quality Assurance
Identify data quality issues in FHIR records.

## Command Line Usage

```bash
# Convert a FHIR bundle file
python -m aibroker.fhir_reader.timeline patient_data.json
```

## Integration with FHIR Servers

### HAPI FHIR Server

```python
import requests
from aibroker.fhir_reader import convert_fhir_bundle_to_timeline

# Get everything for a patient
response = requests.get('http://localhost:8080/fhir/Patient/123/$everything')
bundle = response.json()

timeline = convert_fhir_bundle_to_timeline(bundle)
```

### Azure FHIR Service

```python
import requests
from aibroker.fhir_reader import convert_fhir_bundle_to_timeline

headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(
    'https://your-fhir-service.azurehealthcareapis.com/Patient/123/$everything',
    headers=headers
)
bundle = response.json()

timeline = convert_fhir_bundle_to_timeline(bundle)
```

## Why Chronological Format?

Traditional FHIR bundles group resources by type (all encounters together, all medications together, etc.). This makes it difficult to understand the patient's journey and spot inconsistencies.

**Before (FHIR Bundle):**
```
Bundle
├── Patient
├── Encounters (5 encounters)
├── Conditions (3 conditions)
├── Medications (7 medications)
└── Allergies (2 allergies)
```

**After (Timeline):**
```
1983-04-25: First visit for problem
1983-05-15: Allergy diagnosed
1983-05-15: Medication prescribed
2000-12-03: General examination
```

The chronological format makes it immediately clear what happened when, making it much easier to spot issues like:
- Medication prescribed before the condition was diagnosed
- Missing follow-ups after serious diagnoses
- Allergies recorded after medications prescribed

## LLM Integration Example

```python
from aibroker.fhir_reader import load_and_convert
import anthropic  # or openai, etc.

# Convert FHIR to timeline
timeline = load_and_convert('patient_data.json')

# Send to Claude/GPT for analysis
client = anthropic.Anthropic(api_key="your-api-key")
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": f"""Review this patient timeline for inconsistencies:

{timeline}

Identify any medical logic issues, timeline problems, or concerning patterns."""
    }]
)

print(message.content[0].text)
```

## Requirements

- Python 3.7+
- No external dependencies for core functionality
- `requests` library only needed for FHIR API examples

## License

MIT License

## Contributing

Contributions welcome! This library is designed to be extended with additional FHIR resource types and formatting options.

## Future Enhancements

Potential additions:
- Support for more FHIR resource types
- Customizable output formats (Markdown, HTML, etc.)
- Timeline visualization
- Automated consistency rules
- FHIR R4/R5 version support indicators
- Multi-patient timeline comparisons

## Author

Created for healthcare data analysis and AI-powered medical record review.

## Related Resources

- [FHIR Specification](https://www.hl7.org/fhir/)
- [HAPI FHIR](https://hapifhir.io/)
- [Synthea - Synthetic Patient Data](https://synthetichealth.github.io/synthea/)
