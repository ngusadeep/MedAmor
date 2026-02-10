"""
FHIR to LLM-Friendly Timeline Converter

This library takes FHIR Bundle resources and converts them into a chronological
narrative format that's easy for LLMs to review for consistency.

Author: Assistant
License: MIT
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import base64


class FHIRTimelineConverter:
    """
    Converts FHIR Bundle data into chronological, narrative format for LLM review.
    """

    def __init__(self, bundle: Dict[str, Any]):
        """
        Initialize with a FHIR Bundle.

        Args:
            bundle: FHIR Bundle resource (dict)
        """
        self.bundle = bundle
        self.patient_info = None
        self.timeline_events = []

    def convert(self, include_costs: bool = True, include_codes: bool = False) -> str:
        """
        Convert FHIR bundle to chronological narrative.

        Args:
            include_costs: Include cost information in output
            include_codes: Include medical codes (SNOMED, LOINC, etc.)

        Returns:
            Formatted string with chronological patient history
        """
        # Extract patient demographics
        self._extract_patient_info()

        # Process all resources and extract temporal events
        self._process_bundle()

        # Sort events chronologically
        self.timeline_events.sort(key=lambda x: x['datetime'])

        # Format as narrative
        return self._format_narrative(include_costs, include_codes)

    def _extract_patient_info(self) -> None:
        """Extract patient demographic information."""
        if 'entry' not in self.bundle:
            return

        for entry in self.bundle['entry']:
            resource = entry.get('resource', {})
            if resource.get('resourceType') == 'Patient':
                self.patient_info = self._parse_patient(resource)
                break

    def _parse_patient(self, patient: Dict) -> Dict:
        """Parse patient resource into readable format."""
        info = {
            'id': patient.get('id', 'Unknown'),
            'birth_date': patient.get('birthDate', 'Unknown'),
            'gender': patient.get('gender', 'Unknown'),
            'name': 'Unknown',
            'address': None,
            'phone': None,
            'marital_status': None,
            'race': None,
            'ethnicity': None
        }

        # Parse name
        if 'name' in patient and len(patient['name']) > 0:
            name_obj = patient['name'][0]
            prefix = ' '.join(name_obj.get('prefix', []))
            given = ' '.join(name_obj.get('given', []))
            family = name_obj.get('family', '')
            info['name'] = f"{prefix} {given} {family}".strip()

        # Parse address
        if 'address' in patient and len(patient['address']) > 0:
            addr = patient['address'][0]
            line = ', '.join(addr.get('line', []))
            city = addr.get('city', '')
            state = addr.get('state', '')
            postal = addr.get('postalCode', '')
            info['address'] = f"{line}, {city}, {state} {postal}".strip(', ')

        # Parse phone
        if 'telecom' in patient:
            for telecom in patient['telecom']:
                if telecom.get('system') == 'phone':
                    info['phone'] = telecom.get('value')
                    break

        # Parse marital status
        if 'maritalStatus' in patient:
            marital = patient['maritalStatus']
            if 'text' in marital:
                info['marital_status'] = marital['text']
            elif 'coding' in marital and len(marital['coding']) > 0:
                info['marital_status'] = marital['coding'][0].get('display')

        # Parse extensions (race, ethnicity)
        if 'extension' in patient:
            for ext in patient['extension']:
                url = ext.get('url', '')
                if 'race' in url.lower():
                    for sub_ext in ext.get('extension', []):
                        if sub_ext.get('url') == 'text':
                            info['race'] = sub_ext.get('valueString')
                elif 'ethnicity' in url.lower():
                    for sub_ext in ext.get('extension', []):
                        if sub_ext.get('url') == 'text':
                            info['ethnicity'] = sub_ext.get('valueString')

        return info

    def _process_bundle(self) -> None:
        """Process all bundle entries and extract temporal events."""
        if 'entry' not in self.bundle:
            return

        for entry in self.bundle['entry']:
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType')

            # Dispatch to appropriate parser
            if resource_type == 'Encounter':
                self._process_encounter(resource)
            elif resource_type == 'Condition':
                self._process_condition(resource)
            elif resource_type == 'AllergyIntolerance':
                self._process_allergy(resource)
            elif resource_type == 'MedicationRequest':
                self._process_medication(resource)
            elif resource_type == 'Observation':
                self._process_observation(resource)
            elif resource_type == 'Procedure':
                self._process_procedure(resource)
            elif resource_type == 'Immunization':
                self._process_immunization(resource)
            elif resource_type == 'DiagnosticReport':
                self._process_diagnostic_report(resource)
            elif resource_type == 'CarePlan':
                self._process_care_plan(resource)
            elif resource_type == 'Claim':
                self._process_claim(resource)
            elif resource_type == 'MedicationAdministration':
                self._process_medication_administration(resource)
            elif resource_type == 'MedicationStatement':
                self._process_medication_statement(resource)
            elif resource_type == 'Goal':
                self._process_goal(resource)
            elif resource_type == 'ServiceRequest':
                self._process_service_request(resource)
            elif resource_type == 'Device':
                self._process_device(resource)
            elif resource_type == 'DeviceUseStatement':
                self._process_device_use(resource)
            elif resource_type == 'Appointment':
                self._process_appointment(resource)
            elif resource_type == 'FamilyMemberHistory':
                self._process_family_history(resource)
            elif resource_type == 'DocumentReference':
                self._process_document_reference(resource)
            elif resource_type == 'Practitioner':
                self._process_practitioner(resource)
            elif resource_type == 'PractitionerRole':
                self._process_practitioner_role(resource)
            elif resource_type == 'Organization':
                self._process_organization(resource)
            elif resource_type == 'Location':
                self._process_location(resource)
            elif resource_type == 'ImagingStudy':
                self._process_imaging_study(resource)
            elif resource_type == 'ClinicalImpression':
                self._process_clinical_impression(resource)
            elif resource_type == 'Task':
                self._process_task(resource)
            elif resource_type == 'EpisodeOfCare':
                self._process_episode_of_care(resource)
            elif resource_type == 'Communication':
                self._process_communication(resource)
            elif resource_type == 'CommunicationRequest':
                self._process_communication_request(resource)
            elif resource_type == 'Flag':
                self._process_flag(resource)
            elif resource_type == 'Provenance':
                self._process_provenance(resource)
            elif resource_type == 'AuditEvent':
                self._process_audit_event(resource)

    def _process_encounter(self, encounter: Dict) -> None:
        """Process encounter resource."""
        period = encounter.get('period', {})
        start = period.get('start')
        end = period.get('end')

        if not start:
            return

        # Get encounter type
        enc_type = 'Visit'
        if 'type' in encounter and len(encounter['type']) > 0:
            type_obj = encounter['type'][0]
            if 'text' in type_obj:
                enc_type = type_obj['text']
            elif 'coding' in type_obj and len(type_obj['coding']) > 0:
                enc_type = type_obj['coding'][0].get('display', enc_type)

        # Get class
        enc_class = encounter.get('class', {}).get('code', 'ambulatory')

        # Get practitioner
        practitioner = None
        if 'participant' in encounter:
            for participant in encounter['participant']:
                if 'individual' in participant:
                    practitioner = participant['individual'].get('display')
                    break

        # Get location
        location = None
        if 'location' in encounter and len(encounter['location']) > 0:
            location = encounter['location'][0].get('location', {}).get('display')

        # Get reason
        reason = None
        if 'reasonCode' in encounter and len(encounter['reasonCode']) > 0:
            reason_obj = encounter['reasonCode'][0]
            if 'text' in reason_obj:
                reason = reason_obj['text']
            elif 'coding' in reason_obj and len(reason_obj['coding']) > 0:
                reason = reason_obj['coding'][0].get('display')

        event = {
            'datetime': self._parse_datetime(start),
            'datetime_str': start,
            'end_datetime': self._parse_datetime(end) if end else None,
            'type': 'encounter',
            'enc_id': encounter.get('id'),
            'enc_type': enc_type,
            'enc_class': enc_class,
            'practitioner': practitioner,
            'location': location,
            'reason': reason
        }

        self.timeline_events.append(event)

    def _process_condition(self, condition: Dict) -> None:
        """Process condition/diagnosis resource."""
        onset = None

        # Try various onset fields
        if 'onsetDateTime' in condition:
            onset = condition['onsetDateTime']
        elif 'recordedDate' in condition:
            onset = condition['recordedDate']

        if not onset:
            return

        # Get condition name
        condition_name = 'Unknown condition'
        if 'code' in condition:
            code = condition['code']
            if 'text' in code:
                condition_name = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                condition_name = code['coding'][0].get('display', condition_name)

        # Get clinical status
        status = None
        if 'clinicalStatus' in condition:
            status_obj = condition['clinicalStatus']
            if 'coding' in status_obj and len(status_obj['coding']) > 0:
                status = status_obj['coding'][0].get('code')

        # Get severity
        severity = None
        if 'severity' in condition:
            sev_obj = condition['severity']
            if 'text' in sev_obj:
                severity = sev_obj['text']
            elif 'coding' in sev_obj and len(sev_obj['coding']) > 0:
                severity = sev_obj['coding'][0].get('display')

        event = {
            'datetime': self._parse_datetime(onset),
            'datetime_str': onset,
            'type': 'condition',
            'condition_name': condition_name,
            'status': status,
            'severity': severity
        }

        self.timeline_events.append(event)

    def _process_allergy(self, allergy: Dict) -> None:
        """Process allergy intolerance resource."""
        recorded_date = allergy.get('recordedDate')

        if not recorded_date:
            return

        # Get allergen
        allergen = 'Unknown allergen'
        if 'code' in allergy:
            code = allergy['code']
            if 'text' in code:
                allergen = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                allergen = code['coding'][0].get('display', allergen)

        # Get type and category
        allergy_type = allergy.get('type', 'Unknown')
        category = allergy.get('category', [])
        if category:
            category = category[0] if isinstance(category, list) else category
        else:
            category = 'Unknown'

        # Get criticality
        criticality = allergy.get('criticality', 'Unknown')

        # Get reactions
        reactions = []
        if 'reaction' in allergy:
            for reaction in allergy['reaction']:
                if 'manifestation' in reaction:
                    for manifestation in reaction['manifestation']:
                        if 'text' in manifestation:
                            reactions.append(manifestation['text'])
                        elif 'coding' in manifestation and len(manifestation['coding']) > 0:
                            reactions.append(manifestation['coding'][0].get('display', ''))

        event = {
            'datetime': self._parse_datetime(recorded_date),
            'datetime_str': recorded_date,
            'type': 'allergy',
            'allergen': allergen,
            'allergy_type': allergy_type,
            'category': category,
            'criticality': criticality,
            'reactions': reactions
        }

        self.timeline_events.append(event)

    def _process_medication(self, med_request: Dict) -> None:
        """Process medication request resource."""
        authored_on = med_request.get('authoredOn')

        if not authored_on:
            return

        # Get medication name
        medication = 'Unknown medication'
        if 'medicationCodeableConcept' in med_request:
            med_code = med_request['medicationCodeableConcept']
            if 'text' in med_code:
                medication = med_code['text']
            elif 'coding' in med_code and len(med_code['coding']) > 0:
                medication = med_code['coding'][0].get('display', medication)

        # Get status
        status = med_request.get('status', 'Unknown')

        # Get dosage instructions
        dosage = []
        if 'dosageInstruction' in med_request:
            for dose in med_request['dosageInstruction']:
                if 'text' in dose:
                    dosage.append(dose['text'])

        # Get requester
        requester = None
        if 'requester' in med_request:
            requester = med_request['requester'].get('display')

        event = {
            'datetime': self._parse_datetime(authored_on),
            'datetime_str': authored_on,
            'type': 'medication',
            'medication': medication,
            'status': status,
            'dosage': dosage,
            'requester': requester
        }

        self.timeline_events.append(event)

    def _process_observation(self, observation: Dict) -> None:
        """Process observation resource."""
        effective_dt = observation.get('effectiveDateTime')

        if not effective_dt:
            return

        # Get observation name
        obs_name = 'Unknown observation'
        if 'code' in observation:
            code = observation['code']
            if 'text' in code:
                obs_name = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                obs_name = code['coding'][0].get('display', obs_name)

        # Get value
        value = None
        unit = None

        if 'valueQuantity' in observation:
            val_obj = observation['valueQuantity']
            value = val_obj.get('value')
            unit = val_obj.get('unit', val_obj.get('code'))
        elif 'valueString' in observation:
            value = observation['valueString']
        elif 'valueCodeableConcept' in observation:
            val_obj = observation['valueCodeableConcept']
            if 'text' in val_obj:
                value = val_obj['text']
            elif 'coding' in val_obj and len(val_obj['coding']) > 0:
                value = val_obj['coding'][0].get('display')

        event = {
            'datetime': self._parse_datetime(effective_dt),
            'datetime_str': effective_dt,
            'type': 'observation',
            'observation': obs_name,
            'value': value,
            'unit': unit
        }

        self.timeline_events.append(event)

    def _process_procedure(self, procedure: Dict) -> None:
        """Process procedure resource."""
        performed = procedure.get('performedDateTime')

        if not performed and 'performedPeriod' in procedure:
            performed = procedure['performedPeriod'].get('start')

        if not performed:
            return

        # Get procedure name
        proc_name = 'Unknown procedure'
        if 'code' in procedure:
            code = procedure['code']
            if 'text' in code:
                proc_name = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                proc_name = code['coding'][0].get('display', proc_name)

        # Get status
        status = procedure.get('status', 'Unknown')

        event = {
            'datetime': self._parse_datetime(performed),
            'datetime_str': performed,
            'type': 'procedure',
            'procedure': proc_name,
            'status': status
        }

        self.timeline_events.append(event)

    def _process_immunization(self, immunization: Dict) -> None:
        """Process immunization resource."""
        occurrence = immunization.get('occurrenceDateTime')

        if not occurrence:
            return

        # Get vaccine name
        vaccine = 'Unknown vaccine'
        if 'vaccineCode' in immunization:
            code = immunization['vaccineCode']
            if 'text' in code:
                vaccine = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                vaccine = code['coding'][0].get('display', vaccine)

        # Get status
        status = immunization.get('status', 'Unknown')

        event = {
            'datetime': self._parse_datetime(occurrence),
            'datetime_str': occurrence,
            'type': 'immunization',
            'vaccine': vaccine,
            'status': status
        }

        self.timeline_events.append(event)

    def _process_diagnostic_report(self, report: Dict) -> None:
        """Process diagnostic report resource."""
        effective = report.get('effectiveDateTime')

        if not effective:
            return

        # Get report type
        report_type = 'Diagnostic Report'
        if 'code' in report:
            code = report['code']
            if 'text' in code:
                report_type = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                report_type = code['coding'][0].get('display', report_type)

        # Try to extract text from presentedForm
        text_content = None
        if 'presentedForm' in report and len(report['presentedForm']) > 0:
            form = report['presentedForm'][0]
            if 'data' in form:
                try:
                    decoded = base64.b64decode(form['data']).decode('utf-8')
                    # Limit length
                    if len(decoded) > 500:
                        text_content = decoded[:500] + "... (truncated)"
                    else:
                        text_content = decoded
                except:
                    pass

        event = {
            'datetime': self._parse_datetime(effective),
            'datetime_str': effective,
            'type': 'diagnostic_report',
            'report_type': report_type,
            'text_content': text_content
        }

        self.timeline_events.append(event)

    def _process_care_plan(self, care_plan: Dict) -> None:
        """Process care plan resource."""
        period = care_plan.get('period', {})
        start = period.get('start')

        if not start:
            return

        # Get care plan category
        category = 'Care Plan'
        if 'category' in care_plan and len(care_plan['category']) > 0:
            cat_obj = care_plan['category'][0]
            if 'text' in cat_obj:
                category = cat_obj['text']
            elif 'coding' in cat_obj and len(cat_obj['coding']) > 0:
                category = cat_obj['coding'][0].get('display', category)

        # Get activities
        activities = []
        if 'activity' in care_plan:
            for activity in care_plan['activity']:
                if 'detail' in activity and 'code' in activity['detail']:
                    detail = activity['detail']
                    code = detail['code']
                    activity_name = None

                    if 'text' in code:
                        activity_name = code['text']
                    elif 'coding' in code and len(code['coding']) > 0:
                        activity_name = code['coding'][0].get('display')

                    if activity_name:
                        activities.append(activity_name)

        event = {
            'datetime': self._parse_datetime(start),
            'datetime_str': start,
            'type': 'care_plan',
            'category': category,
            'activities': activities,
            'status': care_plan.get('status', 'Unknown')
        }

        self.timeline_events.append(event)

    def _process_claim(self, claim: Dict) -> None:
        """Process claim resource."""
        created = claim.get('created')

        if not created:
            return

        # Get total amount
        total = None
        currency = None
        if 'total' in claim:
            total_obj = claim['total']
            total = total_obj.get('value')
            currency = total_obj.get('currency', 'USD')

        # Get claim type
        claim_type = 'Claim'
        if 'type' in claim:
            type_obj = claim['type']
            if 'coding' in type_obj and len(type_obj['coding']) > 0:
                claim_type = type_obj['coding'][0].get('code', claim_type)

        event = {
            'datetime': self._parse_datetime(created),
            'datetime_str': created,
            'type': 'claim',
            'claim_type': claim_type,
            'total': total,
            'currency': currency
        }

        self.timeline_events.append(event)

    def _process_medication_administration(self, med_admin: Dict) -> None:
        """Process medication administration resource."""
        effective = med_admin.get('effectiveDateTime')

        if not effective and 'effectivePeriod' in med_admin:
            effective = med_admin['effectivePeriod'].get('start')

        if not effective:
            return

        # Get medication name
        medication = 'Unknown medication'
        if 'medicationCodeableConcept' in med_admin:
            med_code = med_admin['medicationCodeableConcept']
            if 'text' in med_code:
                medication = med_code['text']
            elif 'coding' in med_code and len(med_code['coding']) > 0:
                medication = med_code['coding'][0].get('display', medication)

        # Get status
        status = med_admin.get('status', 'Unknown')

        # Get dosage
        dosage_text = None
        if 'dosage' in med_admin:
            dose = med_admin['dosage']
            if 'text' in dose:
                dosage_text = dose['text']
            elif 'dose' in dose:
                dose_obj = dose['dose']
                value = dose_obj.get('value')
                unit = dose_obj.get('unit', dose_obj.get('code'))
                if value:
                    dosage_text = f"{value} {unit}" if unit else str(value)

        event = {
            'datetime': self._parse_datetime(effective),
            'datetime_str': effective,
            'type': 'medication_administration',
            'medication': medication,
            'status': status,
            'dosage': dosage_text
        }

        self.timeline_events.append(event)

    def _process_medication_statement(self, med_statement: Dict) -> None:
        """Process medication statement resource."""
        effective = med_statement.get('effectiveDateTime')

        if not effective and 'effectivePeriod' in med_statement:
            effective = med_statement['effectivePeriod'].get('start')

        if not effective:
            return

        # Get medication name
        medication = 'Unknown medication'
        if 'medicationCodeableConcept' in med_statement:
            med_code = med_statement['medicationCodeableConcept']
            if 'text' in med_code:
                medication = med_code['text']
            elif 'coding' in med_code and len(med_code['coding']) > 0:
                medication = med_code['coding'][0].get('display', medication)

        # Get status
        status = med_statement.get('status', 'Unknown')

        event = {
            'datetime': self._parse_datetime(effective),
            'datetime_str': effective,
            'type': 'medication_statement',
            'medication': medication,
            'status': status
        }

        self.timeline_events.append(event)

    def _process_goal(self, goal: Dict) -> None:
        """Process goal resource."""
        start_date = None

        if 'startDate' in goal:
            start_date = goal['startDate']
        elif 'statusDate' in goal:
            start_date = goal['statusDate']

        if not start_date:
            return

        # Get goal description
        description = 'Unknown goal'
        if 'description' in goal:
            desc_obj = goal['description']
            if 'text' in desc_obj:
                description = desc_obj['text']
            elif 'coding' in desc_obj and len(desc_obj['coding']) > 0:
                description = desc_obj['coding'][0].get('display', description)

        # Get lifecycle status
        status = goal.get('lifecycleStatus', 'Unknown')

        # Get target date
        target_date = None
        if 'target' in goal and len(goal['target']) > 0:
            target = goal['target'][0]
            if 'dueDate' in target:
                target_date = target['dueDate']

        event = {
            'datetime': self._parse_datetime(start_date),
            'datetime_str': start_date,
            'type': 'goal',
            'description': description,
            'status': status,
            'target_date': target_date
        }

        self.timeline_events.append(event)

    def _process_service_request(self, service_request: Dict) -> None:
        """Process service request resource."""
        authored = service_request.get('authoredOn')

        if not authored:
            return

        # Get service name
        service = 'Unknown service'
        if 'code' in service_request:
            code = service_request['code']
            if 'text' in code:
                service = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                service = code['coding'][0].get('display', service)

        # Get status
        status = service_request.get('status', 'Unknown')

        # Get intent
        intent = service_request.get('intent', 'Unknown')

        # Get requester
        requester = None
        if 'requester' in service_request:
            requester = service_request['requester'].get('display')

        event = {
            'datetime': self._parse_datetime(authored),
            'datetime_str': authored,
            'type': 'service_request',
            'service': service,
            'status': status,
            'intent': intent,
            'requester': requester
        }

        self.timeline_events.append(event)

    def _process_device_use(self, device_use: Dict) -> None:
        """Process device use statement resource."""
        timing = None

        if 'timingDateTime' in device_use:
            timing = device_use['timingDateTime']
        elif 'timingPeriod' in device_use:
            timing = device_use['timingPeriod'].get('start')
        elif 'recordedOn' in device_use:
            timing = device_use['recordedOn']

        if not timing:
            return

        # Get device name
        device_name = 'Unknown device'
        if 'device' in device_use:
            device_ref = device_use['device']
            if 'display' in device_ref:
                device_name = device_ref['display']

        # Get status
        status = device_use.get('status', 'Unknown')

        event = {
            'datetime': self._parse_datetime(timing),
            'datetime_str': timing,
            'type': 'device_use',
            'device': device_name,
            'status': status
        }

        self.timeline_events.append(event)

    def _process_appointment(self, appointment: Dict) -> None:
        """Process appointment resource."""
        start = appointment.get('start')

        if not start:
            return

        # Get appointment type
        appt_type = 'Appointment'
        if 'appointmentType' in appointment:
            type_obj = appointment['appointmentType']
            if 'text' in type_obj:
                appt_type = type_obj['text']
            elif 'coding' in type_obj and len(type_obj['coding']) > 0:
                appt_type = type_obj['coding'][0].get('display', appt_type)

        # Get status
        status = appointment.get('status', 'Unknown')

        # Get participants
        participants = []
        if 'participant' in appointment:
            for participant in appointment['participant']:
                if 'actor' in participant and 'display' in participant['actor']:
                    participants.append(participant['actor']['display'])

        event = {
            'datetime': self._parse_datetime(start),
            'datetime_str': start,
            'type': 'appointment',
            'appt_type': appt_type,
            'status': status,
            'participants': participants
        }

        self.timeline_events.append(event)

    def _process_family_history(self, family_history: Dict) -> None:
        """Process family member history resource."""
        date = family_history.get('date')

        if not date:
            return

        # Get relationship
        relationship = 'Unknown relation'
        if 'relationship' in family_history:
            rel_obj = family_history['relationship']
            if 'text' in rel_obj:
                relationship = rel_obj['text']
            elif 'coding' in rel_obj and len(rel_obj['coding']) > 0:
                relationship = rel_obj['coding'][0].get('display', relationship)

        # Get conditions
        conditions = []
        if 'condition' in family_history:
            for condition in family_history['condition']:
                if 'code' in condition:
                    code = condition['code']
                    cond_name = None
                    if 'text' in code:
                        cond_name = code['text']
                    elif 'coding' in code and len(code['coding']) > 0:
                        cond_name = code['coding'][0].get('display')

                    if cond_name:
                        conditions.append(cond_name)

        event = {
            'datetime': self._parse_datetime(date),
            'datetime_str': date,
            'type': 'family_history',
            'relationship': relationship,
            'conditions': conditions
        }

        self.timeline_events.append(event)

    def _process_document_reference(self, doc_ref: Dict) -> None:
        """Process document reference resource."""
        date = doc_ref.get('date')

        if not date:
            return

        # Get document type
        doc_type = 'Document'
        if 'type' in doc_ref:
            type_obj = doc_ref['type']
            if 'text' in type_obj:
                doc_type = type_obj['text']
            elif 'coding' in type_obj and len(type_obj['coding']) > 0:
                doc_type = type_obj['coding'][0].get('display', doc_type)

        # Get status
        status = doc_ref.get('status', 'Unknown')

        # Get description
        description = doc_ref.get('description')

        event = {
            'datetime': self._parse_datetime(date),
            'datetime_str': date,
            'type': 'document_reference',
            'doc_type': doc_type,
            'status': status,
            'description': description
        }

        self.timeline_events.append(event)

    def _process_device(self, device: Dict) -> None:
        """Process device resource - these don't have timestamps."""
        pass

    def _process_practitioner(self, practitioner: Dict) -> None:
        """Process practitioner resource - no timeline events, just referenced."""
        pass

    def _process_practitioner_role(self, role: Dict) -> None:
        """Process practitioner role - no timeline events, just referenced."""
        pass

    def _process_organization(self, org: Dict) -> None:
        """Process organization - no timeline events, just referenced."""
        pass

    def _process_location(self, location: Dict) -> None:
        """Process location - no timeline events, just referenced."""
        pass

    def _process_imaging_study(self, imaging_study: Dict) -> None:
        """Process imaging study resource."""
        started = imaging_study.get('started')

        if not started:
            return

        # Get modality
        modality = []
        if 'modality' in imaging_study:
            for mod in imaging_study['modality']:
                if 'code' in mod:
                    modality.append(mod['code'])

        # Get description
        description = imaging_study.get('description', 'Imaging study')

        # Get status
        status = imaging_study.get('status', 'Unknown')

        # Get number of series and instances
        num_series = imaging_study.get('numberOfSeries')
        num_instances = imaging_study.get('numberOfInstances')

        event = {
            'datetime': self._parse_datetime(started),
            'datetime_str': started,
            'type': 'imaging_study',
            'description': description,
            'modality': modality,
            'status': status,
            'num_series': num_series,
            'num_instances': num_instances
        }

        self.timeline_events.append(event)

    def _process_clinical_impression(self, impression: Dict) -> None:
        """Process clinical impression resource."""
        date = impression.get('date')

        if not date:
            # Try effective date
            if 'effectiveDateTime' in impression:
                date = impression['effectiveDateTime']
            elif 'effectivePeriod' in impression:
                date = impression['effectivePeriod'].get('start')

        if not date:
            return

        # Get summary
        summary = impression.get('summary', 'Clinical impression')

        # Get status
        status = impression.get('status', 'Unknown')

        # Get findings
        findings = []
        if 'finding' in impression:
            for finding in impression['finding']:
                if 'itemCodeableConcept' in finding:
                    item = finding['itemCodeableConcept']
                    if 'text' in item:
                        findings.append(item['text'])
                    elif 'coding' in item and len(item['coding']) > 0:
                        findings.append(item['coding'][0].get('display', ''))

        event = {
            'datetime': self._parse_datetime(date),
            'datetime_str': date,
            'type': 'clinical_impression',
            'summary': summary,
            'status': status,
            'findings': findings
        }

        self.timeline_events.append(event)

    def _process_task(self, task: Dict) -> None:
        """Process task resource."""
        authored_on = task.get('authoredOn')

        if not authored_on:
            # Try last modified
            authored_on = task.get('lastModified')

        if not authored_on:
            return

        # Get description
        description = 'Task'
        if 'description' in task:
            description = task['description']
        elif 'code' in task:
            code = task['code']
            if 'text' in code:
                description = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                description = code['coding'][0].get('display', description)

        # Get status
        status = task.get('status', 'Unknown')

        # Get intent
        intent = task.get('intent', 'Unknown')

        # Get priority
        priority = task.get('priority')

        event = {
            'datetime': self._parse_datetime(authored_on),
            'datetime_str': authored_on,
            'type': 'task',
            'description': description,
            'status': status,
            'intent': intent,
            'priority': priority
        }

        self.timeline_events.append(event)

    def _process_episode_of_care(self, episode: Dict) -> None:
        """Process episode of care resource."""
        period = episode.get('period', {})
        start = period.get('start')

        if not start:
            return

        # Get status
        status = episode.get('status', 'Unknown')

        # Get type
        episode_type = []
        if 'type' in episode:
            for type_obj in episode['type']:
                if 'text' in type_obj:
                    episode_type.append(type_obj['text'])
                elif 'coding' in type_obj and len(type_obj['coding']) > 0:
                    episode_type.append(type_obj['coding'][0].get('display', ''))

        # Get diagnosis
        diagnoses = []
        if 'diagnosis' in episode:
            for diag in episode['diagnosis']:
                if 'condition' in diag and 'display' in diag['condition']:
                    diagnoses.append(diag['condition']['display'])

        event = {
            'datetime': self._parse_datetime(start),
            'datetime_str': start,
            'type': 'episode_of_care',
            'status': status,
            'episode_type': episode_type,
            'diagnoses': diagnoses
        }

        self.timeline_events.append(event)

    def _process_communication(self, communication: Dict) -> None:
        """Process communication resource."""
        sent = communication.get('sent')

        if not sent:
            # Try received
            sent = communication.get('received')

        if not sent:
            return

        # Get category
        category = []
        if 'category' in communication:
            for cat in communication['category']:
                if 'text' in cat:
                    category.append(cat['text'])
                elif 'coding' in cat and len(cat['coding']) > 0:
                    category.append(cat['coding'][0].get('display', ''))

        # Get status
        status = communication.get('status', 'Unknown')

        # Get topic
        topic = None
        if 'topic' in communication:
            topic_obj = communication['topic']
            if 'text' in topic_obj:
                topic = topic_obj['text']

        # Get payload summary
        payload_summary = None
        if 'payload' in communication and len(communication['payload']) > 0:
            payload = communication['payload'][0]
            if 'contentString' in payload:
                content = payload['contentString']
                payload_summary = content[:100] + '...' if len(content) > 100 else content

        event = {
            'datetime': self._parse_datetime(sent),
            'datetime_str': sent,
            'type': 'communication',
            'category': category,
            'status': status,
            'topic': topic,
            'payload_summary': payload_summary
        }

        self.timeline_events.append(event)

    def _process_communication_request(self, comm_request: Dict) -> None:
        """Process communication request resource."""
        authored_on = comm_request.get('authoredOn')

        if not authored_on:
            return

        # Get category
        category = []
        if 'category' in comm_request:
            for cat in comm_request['category']:
                if 'text' in cat:
                    category.append(cat['text'])
                elif 'coding' in cat and len(cat['coding']) > 0:
                    category.append(cat['coding'][0].get('display', ''))

        # Get status
        status = comm_request.get('status', 'Unknown')

        # Get priority
        priority = comm_request.get('priority')

        event = {
            'datetime': self._parse_datetime(authored_on),
            'datetime_str': authored_on,
            'type': 'communication_request',
            'category': category,
            'status': status,
            'priority': priority
        }

        self.timeline_events.append(event)

    def _process_flag(self, flag: Dict) -> None:
        """Process flag resource."""
        period = flag.get('period', {})
        start = period.get('start')

        if not start:
            return

        # Get code/description
        flag_code = 'Alert'
        if 'code' in flag:
            code = flag['code']
            if 'text' in code:
                flag_code = code['text']
            elif 'coding' in code and len(code['coding']) > 0:
                flag_code = code['coding'][0].get('display', flag_code)

        # Get status
        status = flag.get('status', 'Unknown')

        # Get category
        category = []
        if 'category' in flag:
            for cat in flag['category']:
                if 'text' in cat:
                    category.append(cat['text'])
                elif 'coding' in cat and len(cat['coding']) > 0:
                    category.append(cat['coding'][0].get('display', ''))

        event = {
            'datetime': self._parse_datetime(start),
            'datetime_str': start,
            'type': 'flag',
            'flag_code': flag_code,
            'status': status,
            'category': category
        }

        self.timeline_events.append(event)

    def _process_provenance(self, provenance: Dict) -> None:
        """Process provenance resource."""
        recorded = provenance.get('recorded')

        if not recorded:
            return

        # Get activity
        activity = None
        if 'activity' in provenance:
            activity_obj = provenance['activity']
            if 'text' in activity_obj:
                activity = activity_obj['text']
            elif 'coding' in activity_obj and len(activity_obj['coding']) > 0:
                activity = activity_obj['coding'][0].get('display')

        # Get agents
        agents = []
        if 'agent' in provenance:
            for agent in provenance['agent']:
                if 'who' in agent and 'display' in agent['who']:
                    agents.append(agent['who']['display'])

        event = {
            'datetime': self._parse_datetime(recorded),
            'datetime_str': recorded,
            'type': 'provenance',
            'activity': activity,
            'agents': agents
        }

        self.timeline_events.append(event)

    def _process_audit_event(self, audit: Dict) -> None:
        """Process audit event resource."""
        recorded = audit.get('recorded')

        if not recorded:
            return

        # Get action
        action = audit.get('action', 'Unknown')

        # Get outcome
        outcome = audit.get('outcome')

        # Get type
        event_type = None
        if 'type' in audit:
            type_obj = audit['type']
            if 'display' in type_obj:
                event_type = type_obj['display']
            elif 'code' in type_obj:
                event_type = type_obj['code']

        event = {
            'datetime': self._parse_datetime(recorded),
            'datetime_str': recorded,
            'type': 'audit_event',
            'action': action,
            'event_type': event_type,
            'outcome': outcome
        }

        self.timeline_events.append(event)

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string to datetime object."""
        if not dt_str:
            return None

        try:
            # Handle various ISO formats
            # Remove timezone info for simpler parsing
            dt_str_clean = dt_str.replace('Z', '+00:00')

            # Try to parse with timezone
            if '+' in dt_str_clean or dt_str_clean.endswith('Z'):
                return datetime.fromisoformat(dt_str_clean.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(dt_str_clean)
        except:
            # Fallback: try just the date part
            try:
                return datetime.fromisoformat(dt_str[:10])
            except:
                return None

    def _format_narrative(self, include_costs: bool, include_codes: bool) -> str:
        """Format timeline events as narrative text."""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("PATIENT MEDICAL TIMELINE")
        lines.append("=" * 80)
        lines.append("")

        # Patient demographics
        if self.patient_info:
            lines.append("PATIENT INFORMATION:")
            lines.append(f"  Name: {self.patient_info['name']}")
            lines.append(f"  Patient ID: {self.patient_info['id']}")
            lines.append(f"  Date of Birth: {self.patient_info['birth_date']}")
            lines.append(f"  Gender: {self.patient_info['gender'].capitalize()}")

            if self.patient_info['race']:
                lines.append(f"  Race: {self.patient_info['race']}")
            if self.patient_info['ethnicity']:
                lines.append(f"  Ethnicity: {self.patient_info['ethnicity']}")
            if self.patient_info['marital_status']:
                lines.append(f"  Marital Status: {self.patient_info['marital_status']}")
            if self.patient_info['address']:
                lines.append(f"  Address: {self.patient_info['address']}")
            if self.patient_info['phone']:
                lines.append(f"  Phone: {self.patient_info['phone']}")

            lines.append("")

        # Timeline
        lines.append("CHRONOLOGICAL TIMELINE:")
        lines.append("-" * 80)
        lines.append("")

        if not self.timeline_events:
            lines.append("No timeline events found.")
            return '\n'.join(lines)

        current_date = None

        for event in self.timeline_events:
            dt = event['datetime']
            if not dt:
                continue

            event_date = dt.strftime('%Y-%m-%d')
            event_time = dt.strftime('%H:%M:%S')

            # Add date header if date changed
            if event_date != current_date:
                if current_date is not None:
                    lines.append("")
                lines.append(f"📅 {event_date}")
                lines.append("")
                current_date = event_date

            # Format event based on type
            if event['type'] == 'encounter':
                lines.append(f"  [{event_time}] VISIT: {event['enc_type']}")
                if event['reason']:
                    lines.append(f"    Reason: {event['reason']}")
                if event['practitioner']:
                    lines.append(f"    Provider: {event['practitioner']}")
                if event['location']:
                    lines.append(f"    Location: {event['location']}")
                if event['end_datetime']:
                    end_time = event['end_datetime'].strftime('%H:%M:%S')
                    lines.append(f"    Duration: {event_time} - {end_time}")

            elif event['type'] == 'condition':
                status_str = f" ({event['status']})" if event['status'] else ""
                lines.append(f"  [{event_time}] CONDITION: {event['condition_name']}{status_str}")
                if event['severity']:
                    lines.append(f"    Severity: {event['severity']}")

            elif event['type'] == 'allergy':
                lines.append(f"  [{event_time}] ALLERGY RECORDED: {event['allergen']}")
                lines.append(f"    Type: {event['allergy_type']}, Category: {event['category']}")
                lines.append(f"    Criticality: {event['criticality']}")
                if event['reactions']:
                    lines.append(f"    Reactions: {', '.join(event['reactions'])}")

            elif event['type'] == 'medication':
                lines.append(f"  [{event_time}] MEDICATION PRESCRIBED: {event['medication']}")
                lines.append(f"    Status: {event['status']}")
                if event['dosage']:
                    lines.append(f"    Dosage: {'; '.join(event['dosage'])}")
                if event['requester']:
                    lines.append(f"    Prescribed by: {event['requester']}")

            elif event['type'] == 'observation':
                value_str = ""
                if event['value'] is not None:
                    value_str = f": {event['value']}"
                    if event['unit']:
                        value_str += f" {event['unit']}"
                lines.append(f"  [{event_time}] OBSERVATION: {event['observation']}{value_str}")

            elif event['type'] == 'procedure':
                lines.append(f"  [{event_time}] PROCEDURE: {event['procedure']}")
                lines.append(f"    Status: {event['status']}")

            elif event['type'] == 'immunization':
                lines.append(f"  [{event_time}] IMMUNIZATION: {event['vaccine']}")
                lines.append(f"    Status: {event['status']}")

            elif event['type'] == 'diagnostic_report':
                lines.append(f"  [{event_time}] DIAGNOSTIC REPORT: {event['report_type']}")
                if event['text_content']:
                    lines.append(f"    Content Preview:")
                    # Indent each line of content
                    for content_line in event['text_content'].split('\n')[:10]:
                        if content_line.strip():
                            lines.append(f"      {content_line}")

            elif event['type'] == 'care_plan':
                lines.append(f"  [{event_time}] CARE PLAN: {event['category']}")
                lines.append(f"    Status: {event['status']}")
                if event['activities']:
                    lines.append(f"    Activities:")
                    for activity in event['activities']:
                        lines.append(f"      - {activity}")

            elif event['type'] == 'claim':
                if include_costs and event['total'] is not None:
                    lines.append(f"  [{event_time}] CLAIM: {event['claim_type']}")
                    lines.append(f"    Amount: {event['currency']} {event['total']:.2f}")

            elif event['type'] == 'medication_administration':
                lines.append(f"  [{event_time}] MEDICATION ADMINISTERED: {event['medication']}")
                lines.append(f"    Status: {event['status']}")
                if event['dosage']:
                    lines.append(f"    Dosage: {event['dosage']}")

            elif event['type'] == 'medication_statement':
                lines.append(f"  [{event_time}] MEDICATION REPORTED: {event['medication']}")
                lines.append(f"    Status: {event['status']}")

            elif event['type'] == 'goal':
                lines.append(f"  [{event_time}] GOAL SET: {event['description']}")
                lines.append(f"    Status: {event['status']}")
                if event['target_date']:
                    lines.append(f"    Target: {event['target_date']}")

            elif event['type'] == 'service_request':
                lines.append(f"  [{event_time}] SERVICE REQUESTED: {event['service']}")
                lines.append(f"    Status: {event['status']}, Intent: {event['intent']}")
                if event['requester']:
                    lines.append(f"    Requested by: {event['requester']}")

            elif event['type'] == 'device_use':
                lines.append(f"  [{event_time}] DEVICE USE: {event['device']}")
                lines.append(f"    Status: {event['status']}")

            elif event['type'] == 'appointment':
                lines.append(f"  [{event_time}] APPOINTMENT: {event['appt_type']}")
                lines.append(f"    Status: {event['status']}")
                if event['participants']:
                    lines.append(f"    Participants: {', '.join(event['participants'])}")

            elif event['type'] == 'family_history':
                lines.append(f"  [{event_time}] FAMILY HISTORY: {event['relationship']}")
                if event['conditions']:
                    lines.append(f"    Conditions: {', '.join(event['conditions'])}")

            elif event['type'] == 'document_reference':
                lines.append(f"  [{event_time}] DOCUMENT: {event['doc_type']}")
                lines.append(f"    Status: {event['status']}")
                if event['description']:
                    lines.append(f"    Description: {event['description']}")

            elif event['type'] == 'imaging_study':
                lines.append(f"  [{event_time}] IMAGING STUDY: {event['description']}")
                if event['modality']:
                    lines.append(f"    Modality: {', '.join(event['modality'])}")
                lines.append(f"    Status: {event['status']}")
                if event['num_series']:
                    lines.append(f"    Series: {event['num_series']}, Instances: {event['num_instances']}")

            elif event['type'] == 'clinical_impression':
                lines.append(f"  [{event_time}] CLINICAL IMPRESSION: {event['summary']}")
                lines.append(f"    Status: {event['status']}")
                if event['findings']:
                    lines.append(f"    Findings:")
                    for finding in event['findings'][:5]:  # Limit to first 5
                        lines.append(f"      - {finding}")

            elif event['type'] == 'task':
                lines.append(f"  [{event_time}] TASK: {event['description']}")
                lines.append(f"    Status: {event['status']}, Intent: {event['intent']}")
                if event['priority']:
                    lines.append(f"    Priority: {event['priority']}")

            elif event['type'] == 'episode_of_care':
                lines.append(f"  [{event_time}] EPISODE OF CARE STARTED")
                lines.append(f"    Status: {event['status']}")
                if event['episode_type']:
                    lines.append(f"    Type: {', '.join(event['episode_type'])}")
                if event['diagnoses']:
                    lines.append(f"    Diagnoses: {', '.join(event['diagnoses'])}")

            elif event['type'] == 'communication':
                category_str = ', '.join(event['category']) if event['category'] else 'Communication'
                lines.append(f"  [{event_time}] COMMUNICATION: {category_str}")
                lines.append(f"    Status: {event['status']}")
                if event['topic']:
                    lines.append(f"    Topic: {event['topic']}")
                if event['payload_summary']:
                    lines.append(f"    Content: {event['payload_summary']}")

            elif event['type'] == 'communication_request':
                category_str = ', '.join(event['category']) if event['category'] else 'Communication'
                lines.append(f"  [{event_time}] COMMUNICATION REQUESTED: {category_str}")
                lines.append(f"    Status: {event['status']}")
                if event['priority']:
                    lines.append(f"    Priority: {event['priority']}")

            elif event['type'] == 'flag':
                lines.append(f"  [{event_time}] FLAG/ALERT: {event['flag_code']}")
                lines.append(f"    Status: {event['status']}")
                if event['category']:
                    lines.append(f"    Category: {', '.join(event['category'])}")

            elif event['type'] == 'provenance':
                lines.append(f"  [{event_time}] PROVENANCE: {event['activity'] or 'Record activity'}")
                if event['agents']:
                    lines.append(f"    Agents: {', '.join(event['agents'])}")

            elif event['type'] == 'audit_event':
                lines.append(f"  [{event_time}] AUDIT EVENT: {event['action']}")
                if event['event_type']:
                    lines.append(f"    Type: {event['event_type']}")
                if event['outcome'] is not None:
                    lines.append(f"    Outcome: {event['outcome']}")

            lines.append("")

        lines.append("=" * 80)
        lines.append(f"END OF TIMELINE ({len(self.timeline_events)} events)")
        lines.append("=" * 80)

        return '\n'.join(lines)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about the patient record."""
        stats = {
            'total_events': len(self.timeline_events),
            'event_types': defaultdict(int),
            'date_range': None,
            'encounters': 0,
            'medications': 0,
            'allergies': 0,
            'conditions': 0,
            'procedures': 0
        }

        dates = []
        for event in self.timeline_events:
            stats['event_types'][event['type']] += 1
            if event['datetime']:
                dates.append(event['datetime'])

        if dates:
            dates.sort()
            stats['date_range'] = {
                'start': dates[0].strftime('%Y-%m-%d'),
                'end': dates[-1].strftime('%Y-%m-%d'),
                'span_days': (dates[-1] - dates[0]).days
            }

        stats['encounters'] = stats['event_types']['encounter']
        stats['medications'] = stats['event_types']['medication']
        stats['allergies'] = stats['event_types']['allergy']
        stats['conditions'] = stats['event_types']['condition']
        stats['procedures'] = stats['event_types']['procedure']

        return dict(stats)


def convert_fhir_bundle_to_timeline(bundle_json: str,
                                     include_costs: bool = True,
                                     include_codes: bool = False) -> str:
    """
    Convenience function to convert FHIR bundle JSON to timeline.

    Args:
        bundle_json: FHIR Bundle as JSON string or dict
        include_costs: Include cost information
        include_codes: Include medical codes

    Returns:
        Formatted timeline string
    """
    if isinstance(bundle_json, str):
        bundle = json.loads(bundle_json)
    else:
        bundle = bundle_json

    converter = FHIRTimelineConverter(bundle)
    return converter.convert(include_costs=include_costs, include_codes=include_codes)


def load_and_convert(filepath: str,
                     include_costs: bool = True,
                     include_codes: bool = False) -> str:
    """
    Load FHIR bundle from file and convert to timeline.

    Args:
        filepath: Path to JSON file containing FHIR Bundle
        include_costs: Include cost information
        include_codes: Include medical codes

    Returns:
        Formatted timeline string
    """
    with open(filepath, 'r') as f:
        bundle = json.load(f)

    converter = FHIRTimelineConverter(bundle)
    return converter.convert(include_costs=include_costs, include_codes=include_codes)


def main():
    """CLI entry point for FHIR timeline conversion."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: fhir-timeline <fhir_bundle.json>")
        print("       python -m aibroker.fhir_reader.timeline <fhir_bundle.json>")
        sys.exit(1)

    filepath = sys.argv[1]
    timeline = load_and_convert(filepath)
    print(timeline)


# Example usage
if __name__ == "__main__":
    main()
