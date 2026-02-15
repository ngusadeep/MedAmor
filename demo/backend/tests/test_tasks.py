"""Tests for Celery tasks: run_audit_task, create_scheduled_audit_jobs."""

from datetime import date, datetime, timezone
from uuid import uuid4
from unittest.mock import MagicMock, patch

from app.models.audit_report import AuditReport
from app.models.job import Job, JobStatus
from app.worker.tasks import create_scheduled_audit_jobs, run_audit_task


def test_run_audit_task_job_not_found():
    """When job does not exist, returns error."""
    with patch("app.worker.tasks.SessionLocal") as session_factory:
        session = MagicMock()
        session_factory.return_value = session
        session.query.return_value.filter.return_value.first.return_value = None
        result = run_audit_task(str(uuid4()))
        assert result["ok"] is False
        assert "not found" in result.get("error", "").lower()


def test_run_audit_task_job_not_pending():
    """When job is not PENDING, returns error."""
    job = MagicMock(spec=Job)
    job.id = uuid4()
    job.status = JobStatus.COMPLETED
    job.patient_id = "p1"
    job.export_type = None
    job.audit_type = "breast_cancer_screening"
    with patch("app.worker.tasks.SessionLocal") as session_factory:
        session = MagicMock()
        session_factory.return_value = session
        session.query.return_value.filter.return_value.first.return_value = job
        result = run_audit_task(str(job.id))
        assert result["ok"] is False
        assert "not pending" in result.get("error", "").lower()


def test_run_audit_task_success_creates_report():
    """When job is PENDING, sets IN_PROGRESS, runs audit, saves report, sets COMPLETED."""
    job_id = uuid4()
    job = MagicMock(spec=Job)
    job.id = job_id
    job.status = JobStatus.PENDING
    job.patient_id = "p1"
    job.export_type = None
    job.audit_type = "breast_cancer_screening"
    job.triggered_by = None
    job.error_message = None

    report_create = MagicMock()
    report_create.job_id = job_id
    report_create.patient_id = "p1"
    report_create.status = "NO_FINDINGS"
    report_create.risk_level = None
    report_create.executive_summary = "Summary"
    report_create.findings = []
    report_create.evidence = []
    report_create.corrective_actions = []
    report_create.next_audit_date = None

    with patch("app.worker.tasks.SessionLocal") as session_factory:
        session = MagicMock()
        session_factory.return_value = session
        session.query.return_value.filter.return_value.first.return_value = job
        with patch("app.worker.tasks.run_audit", return_value=report_create):
            result = run_audit_task(str(job_id))
    assert result["ok"] is True
    assert "report_id" in result
    assert job.status == JobStatus.COMPLETED
    session.add.assert_called()
    assert session.commit.call_count >= 2


def test_create_scheduled_audit_jobs_due_and_never_audited():
    """create_scheduled_audit_jobs creates jobs for due + never_audited, skips existing PENDING."""
    report_due = MagicMock(spec=AuditReport)
    report_due.patient_id = "due_patient"
    report_due.next_audit_date = datetime(2026, 2, 1, tzinfo=timezone.utc)
    report_due.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

    report_future = MagicMock(spec=AuditReport)
    report_future.patient_id = "future_patient"
    report_future.next_audit_date = datetime(2026, 3, 1, tzinfo=timezone.utc)
    report_future.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

    all_reports = [report_due, report_future]

    list_patients_result = [
        MagicMock(patient_id="p1"),
        MagicMock(patient_id="due_patient"),
        MagicMock(patient_id="never_audited"),
    ]

    created_jobs = []

    def add_job(job):
        created_jobs.append(job)
        job.id = uuid4()

    fixed_today = date(2026, 2, 2)
    with patch("app.worker.tasks.datetime") as dt_mock:
        dt_mock.now.return_value.date.return_value = fixed_today
        with patch("app.worker.tasks.SessionLocal") as session_factory:
            session = MagicMock()
            session_factory.return_value = session
            session.query.return_value.order_by.return_value.all.return_value = all_reports
            session.query.return_value.filter.return_value.first.return_value = None
            session.add.side_effect = add_job
            with patch("app.worker.tasks.list_patients", return_value=list_patients_result):
                with patch("app.worker.tasks.run_audit_task") as run_audit_task_mock:
                    run_audit_task_mock.delay = MagicMock()
                    out = create_scheduled_audit_jobs()
    assert out["ok"] is True
    assert out["jobs_created"] == 3
    assert out["due"] == 1
    assert out["never_audited"] == 2
    created_patient_ids = {j.patient_id for j in created_jobs}
    assert "due_patient" in created_patient_ids
    assert "p1" in created_patient_ids
    assert "never_audited" in created_patient_ids
