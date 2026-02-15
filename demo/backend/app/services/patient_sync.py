"""Service for syncing patient data from EHR service."""

import asyncio
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.patient import Patient, PatientStatus
from app.schemas.ehr import EHRPatientSummary
from app.services.ehr_client import list_patients_from_service, get_patient_bundle_from_service


async def sync_patients_from_ehr(db: Session) -> dict:
    """Asynchronously sync all patients from EHR service to local database."""
    try:
        # Get all patients from EHR service
        ehr_patients = list_patients_from_service(settings.ehr_service_url)

        synced_count = 0
        updated_count = 0

        for ehr_patient in ehr_patients:
            patient = db.query(Patient).filter(Patient.patient_id == ehr_patient.patient_id).first()

            if patient:
                # Update existing patient
                if patient.patient_name != ehr_patient.patient_name:
                    patient.patient_name = ehr_patient.patient_name
                    patient.updated_at = datetime.now(timezone.utc)
                    updated_count += 1
            else:
                # Create new patient
                patient = Patient(
                    patient_id=ehr_patient.patient_id,
                    patient_name=ehr_patient.patient_name,
                    status=PatientStatus.NEVER_AUDITED,
                    is_active=True
                )
                db.add(patient)
                synced_count += 1

            # Fetch full EHR text for the patient (this can be done in parallel)
            try:
                bundle = get_patient_bundle_from_service(
                    settings.ehr_service_url,
                    ehr_patient.patient_id,
                    "full"
                )
                if bundle and bundle.ehr_text != patient.ehr_text:
                    patient.ehr_text = bundle.ehr_text
                    patient.updated_at = datetime.now(timezone.utc)
            except Exception as e:
                # Log error but continue with other patients
                print(f"Error fetching EHR bundle for {ehr_patient.patient_id}: {e}")

        db.commit()

        return {
            "success": True,
            "synced": synced_count,
            "updated": updated_count,
            "total_patients": len(ehr_patients)
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def update_patient_status_from_reports(db: Session) -> dict:
    """Update patient status based on their latest audit reports."""
    from app.models.audit_report import AuditReport

    patients = db.query(Patient).filter(Patient.is_active == True).all()
    updated_count = 0

    for patient in patients:
        # Get latest audit report for this patient
        latest_report = (
            db.query(AuditReport)
            .filter(AuditReport.patient_id == patient.patient_id)
            .order_by(AuditReport.created_at.desc())
            .first()
        )

        if latest_report:
            # Update patient with latest report data
            patient.last_audit_date = latest_report.created_at
            patient.next_audit_date = latest_report.next_audit_date
            patient.risk_level = latest_report.risk_level

            # Update status based on report and dates
            today = datetime.now(timezone.utc).date()
            next_audit = latest_report.next_audit_date.date() if latest_report.next_audit_date else None

            if latest_report.status == "FINDING_PRESENT":
                patient.status = PatientStatus.NEEDS_ATTENTION
            elif next_audit and next_audit <= today:
                patient.status = PatientStatus.DUE_FOR_REVIEW
            elif next_audit and (next_audit - today).days <= 30:
                patient.status = PatientStatus.RECENTLY_AUDITED
            else:
                patient.status = PatientStatus.COMPLIANT

            patient.updated_at = datetime.now(timezone.utc)
            updated_count += 1
        else:
            # Patient has never been audited
            patient.status = PatientStatus.NEVER_AUDITED
            patient.updated_at = datetime.now(timezone.utc)
            updated_count += 1

    db.commit()
    return {"updated_patients": updated_count}


def get_patients_due_for_review(db: Session) -> List[Patient]:
    """Get patients who are due for review based on their next_audit_date."""
    today = datetime.now(timezone.utc).date()

    return (
        db.query(Patient)
        .filter(
            Patient.is_active == True,
            Patient.status.in_([
                PatientStatus.DUE_FOR_REVIEW,
                PatientStatus.NEVER_AUDITED,
                PatientStatus.NEEDS_ATTENTION
            ])
        )
        .all()
    )