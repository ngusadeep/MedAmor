"""Celery tasks for asynchronous patient audit processing."""

from celery import Task
from .celery_app import celery_app
from .app.agent import build_audit_graph


class AuditTask(Task):
    """Custom task class that initializes the LangGraph once."""

    _graph = None

    @property
    def graph(self):
        """Lazy-load the audit graph (shared across all tasks)."""
        if self._graph is None:
            self._graph = build_audit_graph()
        return self._graph


@celery_app.task(
    bind=True,
    base=AuditTask,
    name="aiorchestrator.tasks.run_patient_audit",
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
)
def run_patient_audit(self, patient_id: str, audit_type: str = "general") -> dict:
    """Run medical audit for a patient (async Celery task).

    Args:
        patient_id: FHIR Patient resource ID
        audit_type: Type of audit (e.g., 'hypertension_compliance', 'diabetes_management')

    Returns:
        dict: Audit result with status, report, and sources

    Raises:
        Exception: Re-raises exceptions after retries exhausted
    """
    try:
        # Update task state to show progress
        self.update_state(
            state="PROCESSING",
            meta={
                "patient_id": patient_id,
                "audit_type": audit_type,
                "stage": "Initializing audit workflow",
            },
        )

        # Run the audit through LangGraph
        graph = self.graph
        result = graph.invoke({
            "patient_id": patient_id.strip(),
            "audit_type": audit_type.strip(),
        })

        # Return successful result
        return {
            "status": "success",
            "patient_id": patient_id,
            "audit_type": audit_type,
            "report": result.get("report", ""),
            "sources": result.get("context") or [],
        }

    except Exception as e:
        # Log the error
        error_msg = f"Audit failed for patient {patient_id}: {str(e)}"
        print(f"ERROR: {error_msg}")

        # Retry the task if retries remaining
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        # Return error result after exhausting retries
        return {
            "status": "error",
            "patient_id": patient_id,
            "audit_type": audit_type,
            "message": error_msg,
            "report": None,
            "sources": [],
        }
