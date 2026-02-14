"""Flask app for MedAudit Backend with async task queue."""

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS
from celery.result import AsyncResult

from aiorchestrator.tasks import run_patient_audit
from aiorchestrator.celery_app import celery_app

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route("/audit", methods=["POST"])
def submit_audit():
    """Submit a patient audit job to the queue.

    Payload: {patient_id, audit_type}
    Returns: {job_id, status, message}
    """
    data = request.get_json() or {}
    patient_id = data.get("patient_id") or ""
    audit_type = data.get("audit_type") or "general"

    if not patient_id:
        return jsonify({"status": "error", "message": "patient_id is required"}), 400

    try:
        # Submit task to Celery queue
        task = run_patient_audit.apply_async(
            args=[patient_id.strip(), audit_type.strip()]
        )

        return jsonify({
            "status": "queued",
            "job_id": task.id,
            "patient_id": patient_id,
            "audit_type": audit_type,
            "message": "Audit job queued successfully",
            "check_status": f"/audit/{task.id}",
        }), 202  # HTTP 202 Accepted

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to queue audit job: {str(e)}",
        }), 500


@app.route("/audit/<job_id>", methods=["GET"])
def get_audit_status(job_id):
    """Get status of an audit job.

    Returns:
        - PENDING: Job is waiting in queue
        - PROCESSING: Job is being processed
        - SUCCESS: Job completed successfully
        - FAILURE: Job failed
    """
    try:
        task = AsyncResult(job_id, app=celery_app)

        if task.state == "PENDING":
            response = {
                "status": "pending",
                "state": "PENDING",
                "job_id": job_id,
                "message": "Audit job is waiting in queue",
            }
        elif task.state == "PROCESSING":
            response = {
                "status": "processing",
                "state": "PROCESSING",
                "job_id": job_id,
                "message": "Audit is being processed",
                "meta": task.info,  # Progress info
            }
        elif task.state == "SUCCESS":
            result = task.result
            response = {
                "status": "completed",
                "state": "SUCCESS",
                "job_id": job_id,
                "result": result,
            }
        elif task.state == "FAILURE":
            response = {
                "status": "failed",
                "state": "FAILURE",
                "job_id": job_id,
                "message": str(task.info),  # Exception info
            }
        else:
            response = {
                "status": task.state.lower(),
                "state": task.state,
                "job_id": job_id,
                "message": f"Job is in state: {task.state}",
            }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get job status: {str(e)}",
        }), 500


@app.route("/audit/<job_id>/result", methods=["GET"])
def get_audit_result(job_id):
    """Get the result of a completed audit job.

    Returns:
        - 200: Result available
        - 202: Job still processing
        - 404: Job not found or failed
    """
    try:
        task = AsyncResult(job_id, app=celery_app)

        if task.state == "SUCCESS":
            return jsonify(task.result), 200
        elif task.state in ["PENDING", "PROCESSING"]:
            return jsonify({
                "status": "processing",
                "message": "Audit is still being processed",
                "job_id": job_id,
            }), 202
        elif task.state == "FAILURE":
            return jsonify({
                "status": "failed",
                "message": "Audit job failed",
                "error": str(task.info),
            }), 404
        else:
            return jsonify({
                "status": task.state.lower(),
                "message": f"Job is in state: {task.state}",
            }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


@app.route("/queue/stats", methods=["GET"])
def queue_stats():
    """Get queue statistics and worker status."""
    try:
        # Get Celery inspector
        inspect = celery_app.control.inspect()

        # Get active tasks
        active = inspect.active()
        reserved = inspect.reserved()
        stats = inspect.stats()

        active_count = sum(len(tasks) for tasks in (active or {}).values())
        reserved_count = sum(len(tasks) for tasks in (reserved or {}).values())
        workers = list((stats or {}).keys())

        return jsonify({
            "workers": {
                "count": len(workers),
                "names": workers,
            },
            "queue": {
                "active_jobs": active_count,
                "queued_jobs": reserved_count,
            },
            "details": {
                "active_tasks": active,
                "reserved_tasks": reserved,
            },
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get queue stats: {str(e)}",
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


def main():
    import os
    port = int(os.environ.get("FLASK_RUN_PORT", 5001))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
