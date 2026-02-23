"""FHIR R4 Bundle → LLM-friendly chronological timeline converter."""

import base64
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class FHIRTimelineConverter:
    """Convert a FHIR R4 Bundle into a chronological narrative for LLM audit."""

    def __init__(self, bundle: dict[str, Any]):
        self.bundle = bundle
        self.patient_info: dict | None = None
        self.timeline_events: list[dict] = []

    # ------------------------------------------------------------------ public

    def convert(self, include_costs: bool = True, include_codes: bool = False) -> str:
        self._extract_patient_info()
        self._process_bundle()
        self.timeline_events.sort(key=lambda x: x["datetime"] or datetime.min)
        return self._format_narrative(include_costs, include_codes)

    def get_summary_stats(self) -> dict[str, Any]:
        stats: dict[str, Any] = {
            "total_events": len(self.timeline_events),
            "event_types": defaultdict(int),
            "date_range": None,
            "encounters": 0,
            "medications": 0,
            "allergies": 0,
            "conditions": 0,
            "procedures": 0,
        }
        dates = []
        for event in self.timeline_events:
            stats["event_types"][event["type"]] += 1
            if event["datetime"]:
                dates.append(event["datetime"])
        if dates:
            dates.sort()
            stats["date_range"] = {
                "start": dates[0].strftime("%Y-%m-%d"),
                "end": dates[-1].strftime("%Y-%m-%d"),
                "span_days": (dates[-1] - dates[0]).days,
            }
        for key in ("encounters", "medications", "allergies", "conditions", "procedures"):
            stats[key] = stats["event_types"][key]
        return dict(stats)

    # --------------------------------------------------------- patient parsing

    def _extract_patient_info(self) -> None:
        for entry in self.bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                self.patient_info = self._parse_patient(resource)
                break

    def _parse_patient(self, patient: dict) -> dict:
        info: dict[str, Any] = {
            "id": patient.get("id", "Unknown"),
            "birth_date": patient.get("birthDate", "Unknown"),
            "gender": patient.get("gender", "Unknown"),
            "name": "Unknown",
            "address": None,
            "phone": None,
            "marital_status": None,
            "race": None,
            "ethnicity": None,
        }
        if patient.get("name"):
            n = patient["name"][0]
            parts = n.get("prefix", []) + n.get("given", []) + [n.get("family", "")]
            info["name"] = " ".join(p for p in parts if p).strip()
        if patient.get("address"):
            a = patient["address"][0]
            info["address"] = ", ".join(
                filter(None, [
                    ", ".join(a.get("line", [])),
                    a.get("city"), a.get("state"), a.get("postalCode"),
                ])
            )
        for t in patient.get("telecom", []):
            if t.get("system") == "phone":
                info["phone"] = t.get("value")
                break
        if "maritalStatus" in patient:
            ms = patient["maritalStatus"]
            info["marital_status"] = ms.get("text") or (
                ms.get("coding", [{}])[0].get("display")
            )
        for ext in patient.get("extension", []):
            url = ext.get("url", "").lower()
            for sub in ext.get("extension", []):
                if sub.get("url") == "text":
                    if "race" in url:
                        info["race"] = sub.get("valueString")
                    elif "ethnicity" in url:
                        info["ethnicity"] = sub.get("valueString")
        return info

    # ---------------------------------------------------------- bundle routing

    def _process_bundle(self) -> None:
        dispatch: dict[str, Any] = {
            "Encounter": self._process_encounter,
            "Condition": self._process_condition,
            "AllergyIntolerance": self._process_allergy,
            "MedicationRequest": self._process_medication,
            "Observation": self._process_observation,
            "Procedure": self._process_procedure,
            "Immunization": self._process_immunization,
            "DiagnosticReport": self._process_diagnostic_report,
            "CarePlan": self._process_care_plan,
            "Claim": self._process_claim,
            "MedicationAdministration": self._process_medication_administration,
            "MedicationStatement": self._process_medication_statement,
            "Goal": self._process_goal,
            "ServiceRequest": self._process_service_request,
            "DeviceUseStatement": self._process_device_use,
            "Appointment": self._process_appointment,
            "FamilyMemberHistory": self._process_family_history,
            "DocumentReference": self._process_document_reference,
            "ImagingStudy": self._process_imaging_study,
            "ClinicalImpression": self._process_clinical_impression,
        }
        for entry in self.bundle.get("entry", []):
            resource = entry.get("resource", {})
            rt = resource.get("resourceType")
            if rt in dispatch:
                dispatch[rt](resource)

    # ------------------------------------------------------- resource parsers

    def _add(self, event: dict) -> None:
        self.timeline_events.append(event)

    def _code_text(self, obj: dict, fallback: str = "Unknown") -> str:
        if not obj:
            return fallback
        if "text" in obj:
            return obj["text"]
        codings = obj.get("coding", [])
        if codings:
            return codings[0].get("display") or codings[0].get("code") or fallback
        return fallback

    def _process_encounter(self, r: dict) -> None:
        start = r.get("period", {}).get("start")
        if not start:
            return
        enc_type = self._code_text(r.get("type", [{}])[0] if r.get("type") else {}, "Visit")
        practitioner = next(
            (p["individual"].get("display") for p in r.get("participant", []) if "individual" in p),
            None,
        )
        location = (r.get("location") or [{}])[0].get("location", {}).get("display")
        reason_obj = (r.get("reasonCode") or [{}])[0]
        reason = self._code_text(reason_obj) if reason_obj else None
        end = r.get("period", {}).get("end")
        self._add({
            "datetime": self._parse_dt(start), "datetime_str": start,
            "end_datetime": self._parse_dt(end) if end else None,
            "type": "encounter", "enc_type": enc_type,
            "enc_class": r.get("class", {}).get("code", "ambulatory"),
            "practitioner": practitioner, "location": location, "reason": reason,
        })

    def _process_condition(self, r: dict) -> None:
        onset = r.get("onsetDateTime") or r.get("recordedDate")
        if not onset:
            return
        status = (r.get("clinicalStatus", {}).get("coding") or [{}])[0].get("code")
        self._add({
            "datetime": self._parse_dt(onset), "datetime_str": onset,
            "type": "condition",
            "condition_name": self._code_text(r.get("code", {})),
            "status": status,
            "severity": self._code_text(r.get("severity", {})) if "severity" in r else None,
        })

    def _process_allergy(self, r: dict) -> None:
        date = r.get("recordedDate")
        if not date:
            return
        reactions = [
            self._code_text(m)
            for rxn in r.get("reaction", [])
            for m in rxn.get("manifestation", [])
        ]
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "allergy",
            "allergen": self._code_text(r.get("code", {}), "Unknown allergen"),
            "allergy_type": r.get("type", "Unknown"),
            "category": (r.get("category") or ["Unknown"])[0],
            "criticality": r.get("criticality", "Unknown"),
            "reactions": reactions,
        })

    def _process_medication(self, r: dict) -> None:
        date = r.get("authoredOn")
        if not date:
            return
        dosage = [d["text"] for d in r.get("dosageInstruction", []) if "text" in d]
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "medication",
            "medication": self._code_text(r.get("medicationCodeableConcept", {}), "Unknown medication"),
            "status": r.get("status", "Unknown"),
            "dosage": dosage,
            "requester": r.get("requester", {}).get("display"),
        })

    def _process_observation(self, r: dict) -> None:
        date = r.get("effectiveDateTime")
        if not date:
            return
        value, unit = None, None
        if "valueQuantity" in r:
            value = r["valueQuantity"].get("value")
            unit = r["valueQuantity"].get("unit") or r["valueQuantity"].get("code")
        elif "valueString" in r:
            value = r["valueString"]
        elif "valueCodeableConcept" in r:
            value = self._code_text(r["valueCodeableConcept"])
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "observation",
            "observation": self._code_text(r.get("code", {}), "Unknown observation"),
            "value": value, "unit": unit,
        })

    def _process_procedure(self, r: dict) -> None:
        date = r.get("performedDateTime") or r.get("performedPeriod", {}).get("start")
        if not date:
            return
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "procedure",
            "procedure": self._code_text(r.get("code", {}), "Unknown procedure"),
            "status": r.get("status", "Unknown"),
        })

    def _process_immunization(self, r: dict) -> None:
        date = r.get("occurrenceDateTime")
        if not date:
            return
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "immunization",
            "vaccine": self._code_text(r.get("vaccineCode", {}), "Unknown vaccine"),
            "status": r.get("status", "Unknown"),
        })

    def _process_diagnostic_report(self, r: dict) -> None:
        date = r.get("effectiveDateTime")
        if not date:
            return
        text_content = None
        forms = r.get("presentedForm", [])
        if forms and "data" in forms[0]:
            try:
                decoded = base64.b64decode(forms[0]["data"]).decode("utf-8")
                text_content = decoded[:500] + ("..." if len(decoded) > 500 else "")
            except Exception:
                pass
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "diagnostic_report",
            "report_type": self._code_text(r.get("code", {}), "Diagnostic Report"),
            "text_content": text_content,
        })

    def _process_care_plan(self, r: dict) -> None:
        start = r.get("period", {}).get("start")
        if not start:
            return
        activities = []
        for act in r.get("activity", []):
            detail = act.get("detail", {})
            if "code" in detail:
                activities.append(self._code_text(detail["code"]))
        self._add({
            "datetime": self._parse_dt(start), "datetime_str": start,
            "type": "care_plan",
            "category": self._code_text((r.get("category") or [{}])[0], "Care Plan"),
            "activities": activities,
            "status": r.get("status", "Unknown"),
        })

    def _process_claim(self, r: dict) -> None:
        date = r.get("created")
        if not date:
            return
        total_obj = r.get("total", {})
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "claim",
            "claim_type": (r.get("type", {}).get("coding") or [{}])[0].get("code", "Claim"),
            "total": total_obj.get("value"),
            "currency": total_obj.get("currency", "USD"),
        })

    def _process_medication_administration(self, r: dict) -> None:
        date = r.get("effectiveDateTime") or r.get("effectivePeriod", {}).get("start")
        if not date:
            return
        dose = r.get("dosage", {})
        dosage_text = dose.get("text")
        if not dosage_text and "dose" in dose:
            d = dose["dose"]
            dosage_text = f"{d.get('value', '')} {d.get('unit', d.get('code', ''))}".strip()
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "medication_administration",
            "medication": self._code_text(r.get("medicationCodeableConcept", {}), "Unknown medication"),
            "status": r.get("status", "Unknown"),
            "dosage": dosage_text,
        })

    def _process_medication_statement(self, r: dict) -> None:
        date = r.get("effectiveDateTime") or r.get("effectivePeriod", {}).get("start")
        if not date:
            return
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "medication_statement",
            "medication": self._code_text(r.get("medicationCodeableConcept", {}), "Unknown medication"),
            "status": r.get("status", "Unknown"),
        })

    def _process_goal(self, r: dict) -> None:
        date = r.get("startDate") or r.get("statusDate")
        if not date:
            return
        target_date = (r.get("target") or [{}])[0].get("dueDate")
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "goal",
            "description": self._code_text(r.get("description", {}), "Unknown goal"),
            "status": r.get("lifecycleStatus", "Unknown"),
            "target_date": target_date,
        })

    def _process_service_request(self, r: dict) -> None:
        date = r.get("authoredOn")
        if not date:
            return
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "service_request",
            "service": self._code_text(r.get("code", {}), "Unknown service"),
            "status": r.get("status", "Unknown"),
            "intent": r.get("intent", "Unknown"),
            "requester": r.get("requester", {}).get("display"),
        })

    def _process_device_use(self, r: dict) -> None:
        date = (
            r.get("timingDateTime")
            or r.get("timingPeriod", {}).get("start")
            or r.get("recordedOn")
        )
        if not date:
            return
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "device_use",
            "device": r.get("device", {}).get("display", "Unknown device"),
            "status": r.get("status", "Unknown"),
        })

    def _process_appointment(self, r: dict) -> None:
        start = r.get("start")
        if not start:
            return
        participants = [
            p["actor"]["display"]
            for p in r.get("participant", [])
            if "actor" in p and "display" in p["actor"]
        ]
        self._add({
            "datetime": self._parse_dt(start), "datetime_str": start,
            "type": "appointment",
            "appt_type": self._code_text(r.get("appointmentType", {}), "Appointment"),
            "status": r.get("status", "Unknown"),
            "participants": participants,
        })

    def _process_family_history(self, r: dict) -> None:
        date = r.get("date")
        if not date:
            return
        conditions = [
            self._code_text(c.get("code", {}))
            for c in r.get("condition", [])
            if "code" in c
        ]
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "family_history",
            "relationship": self._code_text(r.get("relationship", {}), "Unknown relation"),
            "conditions": conditions,
        })

    def _process_document_reference(self, r: dict) -> None:
        date = r.get("date")
        if not date:
            return
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "document_reference",
            "doc_type": self._code_text(r.get("type", {}), "Document"),
            "status": r.get("status", "Unknown"),
            "description": r.get("description"),
        })

    def _process_imaging_study(self, r: dict) -> None:
        started = r.get("started")
        if not started:
            return
        modality = [m.get("code") for m in r.get("modality", []) if "code" in m]
        self._add({
            "datetime": self._parse_dt(started), "datetime_str": started,
            "type": "imaging_study",
            "description": r.get("description", "Imaging study"),
            "modality": modality,
            "status": r.get("status", "Unknown"),
            "num_series": r.get("numberOfSeries"),
            "num_instances": r.get("numberOfInstances"),
        })

    def _process_clinical_impression(self, r: dict) -> None:
        date = (
            r.get("date")
            or r.get("effectiveDateTime")
            or r.get("effectivePeriod", {}).get("start")
        )
        if not date:
            return
        findings = [
            self._code_text(f.get("itemCodeableConcept", {}))
            for f in r.get("finding", [])
            if "itemCodeableConcept" in f
        ]
        self._add({
            "datetime": self._parse_dt(date), "datetime_str": date,
            "type": "clinical_impression",
            "summary": r.get("summary", "Clinical impression"),
            "status": r.get("status", "Unknown"),
            "findings": findings,
        })

    # ------------------------------------------------------------- formatting

    def _parse_dt(self, dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            clean = dt_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean)
        except ValueError:
            try:
                return datetime.fromisoformat(dt_str[:10])
            except ValueError:
                return None

    def _format_narrative(self, include_costs: bool, include_codes: bool) -> str:
        lines: list[str] = []
        lines += ["=" * 80, "PATIENT MEDICAL TIMELINE", "=" * 80, ""]

        if self.patient_info:
            p = self.patient_info
            lines.append("PATIENT INFORMATION:")
            lines.append(f"  Name:           {p['name']}")
            lines.append(f"  Patient ID:     {p['id']}")
            lines.append(f"  Date of Birth:  {p['birth_date']}")
            lines.append(f"  Gender:         {p['gender'].capitalize() if p['gender'] else 'Unknown'}")
            for label, key in [
                ("Race", "race"), ("Ethnicity", "ethnicity"),
                ("Marital Status", "marital_status"),
                ("Address", "address"), ("Phone", "phone"),
            ]:
                if p.get(key):
                    lines.append(f"  {label+':':<16}{p[key]}")
            lines.append("")

        lines += ["CHRONOLOGICAL TIMELINE:", "-" * 80, ""]

        if not self.timeline_events:
            lines.append("No timeline events found.")
            return "\n".join(lines)

        current_date: str | None = None
        for event in self.timeline_events:
            dt = event["datetime"]
            if not dt:
                continue
            event_date = dt.strftime("%Y-%m-%d")
            event_time = dt.strftime("%H:%M:%S")

            if event_date != current_date:
                if current_date is not None:
                    lines.append("")
                lines.append(f"  {event_date}")
                lines.append("")
                current_date = event_date

            t = event["type"]

            if t == "encounter":
                lines.append(f"  [{event_time}] VISIT: {event['enc_type']}")
                if event.get("reason"):
                    lines.append(f"    Reason: {event['reason']}")
                if event.get("practitioner"):
                    lines.append(f"    Provider: {event['practitioner']}")
                if event.get("location"):
                    lines.append(f"    Location: {event['location']}")
                if event.get("end_datetime"):
                    lines.append(f"    End: {event['end_datetime'].strftime('%H:%M:%S')}")

            elif t == "condition":
                status = f" ({event['status']})" if event.get("status") else ""
                lines.append(f"  [{event_time}] CONDITION: {event['condition_name']}{status}")
                if event.get("severity"):
                    lines.append(f"    Severity: {event['severity']}")

            elif t == "allergy":
                lines.append(f"  [{event_time}] ALLERGY: {event['allergen']}")
                lines.append(f"    Type: {event['allergy_type']} | Category: {event['category']} | Criticality: {event['criticality']}")
                if event.get("reactions"):
                    lines.append(f"    Reactions: {', '.join(event['reactions'])}")

            elif t == "medication":
                lines.append(f"  [{event_time}] MEDICATION PRESCRIBED: {event['medication']}")
                lines.append(f"    Status: {event['status']}")
                if event.get("dosage"):
                    lines.append(f"    Dosage: {'; '.join(event['dosage'])}")
                if event.get("requester"):
                    lines.append(f"    Prescribed by: {event['requester']}")

            elif t == "observation":
                value_str = ""
                if event.get("value") is not None:
                    value_str = f": {event['value']}"
                    if event.get("unit"):
                        value_str += f" {event['unit']}"
                lines.append(f"  [{event_time}] OBSERVATION: {event['observation']}{value_str}")

            elif t == "procedure":
                lines.append(f"  [{event_time}] PROCEDURE: {event['procedure']} ({event['status']})")

            elif t == "immunization":
                lines.append(f"  [{event_time}] IMMUNIZATION: {event['vaccine']} ({event['status']})")

            elif t == "diagnostic_report":
                lines.append(f"  [{event_time}] DIAGNOSTIC REPORT: {event['report_type']}")
                if event.get("text_content"):
                    for content_line in event["text_content"].split("\n")[:5]:
                        if content_line.strip():
                            lines.append(f"    {content_line}")

            elif t == "care_plan":
                lines.append(f"  [{event_time}] CARE PLAN: {event['category']} ({event['status']})")
                for act in event.get("activities", []):
                    lines.append(f"    - {act}")

            elif t == "claim":
                if include_costs and event.get("total") is not None:
                    lines.append(f"  [{event_time}] CLAIM: {event['claim_type']} — {event['currency']} {event['total']:.2f}")

            elif t == "medication_administration":
                lines.append(f"  [{event_time}] MEDICATION ADMINISTERED: {event['medication']} ({event['status']})")
                if event.get("dosage"):
                    lines.append(f"    Dosage: {event['dosage']}")

            elif t == "medication_statement":
                lines.append(f"  [{event_time}] MEDICATION REPORTED: {event['medication']} ({event['status']})")

            elif t == "goal":
                lines.append(f"  [{event_time}] GOAL: {event['description']} ({event['status']})")
                if event.get("target_date"):
                    lines.append(f"    Target: {event['target_date']}")

            elif t == "service_request":
                lines.append(f"  [{event_time}] SERVICE REQUESTED: {event['service']} ({event['status']})")
                if event.get("requester"):
                    lines.append(f"    Requested by: {event['requester']}")

            elif t == "device_use":
                lines.append(f"  [{event_time}] DEVICE USE: {event['device']} ({event['status']})")

            elif t == "appointment":
                lines.append(f"  [{event_time}] APPOINTMENT: {event['appt_type']} ({event['status']})")
                if event.get("participants"):
                    lines.append(f"    Participants: {', '.join(event['participants'])}")

            elif t == "family_history":
                lines.append(f"  [{event_time}] FAMILY HISTORY: {event['relationship']}")
                if event.get("conditions"):
                    lines.append(f"    Conditions: {', '.join(event['conditions'])}")

            elif t == "document_reference":
                lines.append(f"  [{event_time}] DOCUMENT: {event['doc_type']} ({event['status']})")
                if event.get("description"):
                    lines.append(f"    {event['description']}")

            elif t == "imaging_study":
                lines.append(f"  [{event_time}] IMAGING: {event['description']}")
                if event.get("modality"):
                    lines.append(f"    Modality: {', '.join(event['modality'])}")

            elif t == "clinical_impression":
                lines.append(f"  [{event_time}] CLINICAL IMPRESSION: {event['summary']} ({event['status']})")
                for finding in event.get("findings", [])[:5]:
                    lines.append(f"    - {finding}")

            lines.append("")

        lines += [
            "=" * 80,
            f"END OF TIMELINE  ({len(self.timeline_events)} events)",
            "=" * 80,
        ]
        return "\n".join(lines)


# ------------------------------------------------------------------ helpers

def convert_fhir_bundle_to_timeline(
    bundle: "str | dict", include_costs: bool = True, include_codes: bool = False
) -> str:
    if isinstance(bundle, str):
        bundle = json.loads(bundle)
    return FHIRTimelineConverter(bundle).convert(
        include_costs=include_costs, include_codes=include_codes
    )


def load_and_convert(filepath: str, include_costs: bool = True, include_codes: bool = False) -> str:
    with open(filepath) as f:
        bundle = json.load(f)
    return FHIRTimelineConverter(bundle).convert(
        include_costs=include_costs, include_codes=include_codes
    )
