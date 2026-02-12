"""
FHIR Resource Type Definitions

Defines the resource types used for different export profiles:
- Imaging workflows (demo and production)
- Handoff scenarios (demo and production)
"""

# Imaging workflow resource types - minimal demo set
imaging_resource_types_demo = [
    "Patient",
    "Encounter",
    "DiagnosticReport",
    "Observation",
    "DocumentReference",
    "Condition",
    "ServiceRequest",
]

# Imaging workflow resource types - full production set
imaging_resource_types_prod = [
    "Patient",
    "Encounter",
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Location",
    "DiagnosticReport",
    "ImagingStudy",
    "Observation",
    "ClinicalImpression",
    "Condition",
    "DocumentReference",
    "ServiceRequest",
    "CarePlan",
    "Task",
    "EpisodeOfCare",
    "Provenance",
    "Flag",
]

# Handoff workflow resource types - minimal demo set
handoff_resource_types_demo = [
    "Patient",
    "Encounter",
    "Practitioner",
    "DiagnosticReport",
    "Observation",
    "Condition",
    "DocumentReference",
]

# Handoff workflow resource types - full production set
handoff_resource_types_prod = [
    "Patient",
    "Encounter",
    "EpisodeOfCare",
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Location",
    "DiagnosticReport",
    "Observation",
    "ClinicalImpression",
    "Condition",
    "DocumentReference",
    "CarePlan",
    "Task",
    "Communication",
    "CommunicationRequest",
    "Flag",
    "Provenance",
    "AuditEvent",
]

# Export profile definitions
EXPORT_PROFILES = {
    "full": {
        "name": "Full Content",
        "description": "All FHIR resources",
        "resource_types": None,  # None means all resources
    },
    "handoff_minimal": {
        "name": "Handoff Minimal",
        "description": "Demo handoff resources",
        "resource_types": handoff_resource_types_demo,
    },
    "handoff_complete": {
        "name": "Handoff Complete",
        "description": "Production handoff resources",
        "resource_types": handoff_resource_types_prod,
    },
    "imaging_minimal": {
        "name": "Imaging Minimal",
        "description": "Demo imaging resources",
        "resource_types": imaging_resource_types_demo,
    },
    "imaging_complete": {
        "name": "Imaging Complete",
        "description": "Production imaging resources",
        "resource_types": imaging_resource_types_prod,
    },
}
