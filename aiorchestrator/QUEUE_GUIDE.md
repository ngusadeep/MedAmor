# Task Queue System - User Guide

The AI orchestrator now uses **Celery + Redis** for asynchronous task processing. This allows multiple patient audit requests to be queued and processed efficiently.

---

## Architecture

```
Multiple Clients
      ↓
  POST /audit  →  Redis Queue  →  Celery Workers  →  Process Audits
      ↓
  Job ID returned
      ↓
  GET /audit/{job_id}  →  Check status
      ↓
  GET /audit/{job_id}/result  →  Get completed audit
```

---

## Quick Start

### 1. Start Redis

```bash
# Using Docker (recommended)
docker compose up redis -d

# Or install locally
# Mac: brew install redis && redis-server
# Linux: sudo apt install redis-server && redis-server
```

### 2. Start Celery Worker

In one terminal:

```bash
cd aiorchestrator

# Start Celery worker (processes tasks from queue)
celery -A aiorchestrator.celery_app worker --loglevel=info
```

### 3. Start Flask API

In another terminal:

```bash
cd aiorchestrator
python main.py
```

---

## API Endpoints

### Submit Audit Job

**POST /audit**

Submit a patient for audit. Returns immediately with a job ID.

```bash
curl -X POST http://localhost:5001/audit \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-123",
    "audit_type": "hypertension_compliance"
  }'
```

**Response** (HTTP 202 Accepted):
```json
{
  "status": "queued",
  "job_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "patient_id": "patient-123",
  "audit_type": "hypertension_compliance",
  "message": "Audit job queued successfully",
  "check_status": "/audit/a1b2c3d4-5678-90ab-cdef-1234567890ab"
}
```

---

### Check Job Status

**GET /audit/{job_id}**

Check the current status of an audit job.

```bash
JOB_ID="a1b2c3d4-5678-90ab-cdef-1234567890ab"
curl http://localhost:5001/audit/$JOB_ID
```

**Possible Statuses**:

1. **PENDING** - Job is waiting in queue
```json
{
  "status": "pending",
  "job_id": "...",
  "message": "Audit job is waiting in queue"
}
```

2. **PROCESSING** - Job is being processed
```json
{
  "status": "processing",
  "job_id": "...",
  "message": "Audit is being processed",
  "meta": {
    "patient_id": "patient-123",
    "stage": "Retrieving guidelines"
  }
}
```

3. **COMPLETED** - Job finished successfully
```json
{
  "status": "completed",
  "job_id": "...",
  "result": {
    "status": "success",
    "patient_id": "patient-123",
    "report": "{...}",
    "sources": [...]
  }
}
```

4. **FAILED** - Job failed
```json
{
  "status": "failed",
  "job_id": "...",
  "message": "Error message here"
}
```

---

### Get Audit Result

**GET /audit/{job_id}/result**

Get the completed audit result. Returns 202 if still processing.

```bash
curl http://localhost:5001/audit/$JOB_ID/result
```

**Response** (HTTP 200 if completed):
```json
{
  "status": "success",
  "patient_id": "patient-123",
  "audit_type": "hypertension_compliance",
  "report": "{\"compliant\": false, \"gaps\": [...], \"evidence\": [...]}",
  "sources": ["guideline1", "guideline2", ...]
}
```

---

### Queue Statistics

**GET /queue/stats**

View queue status and worker information.

```bash
curl http://localhost:5001/queue/stats
```

**Response**:
```json
{
  "workers": {
    "count": 2,
    "names": ["celery@worker1", "celery@worker2"]
  },
  "queue": {
    "active_jobs": 3,
    "queued_jobs": 7
  }
}
```

---

## Usage Examples

### Example 1: Submit Multiple Patients

```bash
# Submit 5 patients at once
for i in {1..5}; do
  curl -X POST http://localhost:5001/audit \
    -H "Content-Type: application/json" \
    -d "{\"patient_id\": \"patient-$i\", \"audit_type\": \"general\"}" \
    -s | jq -r '.job_id'
done
```

All 5 jobs are queued instantly and processed by workers in order.

### Example 2: Poll Until Complete

```bash
JOB_ID="your-job-id-here"

# Poll every 2 seconds until complete
while true; do
  STATUS=$(curl -s http://localhost:5001/audit/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  sleep 2
done

# Get result
curl -s http://localhost:5001/audit/$JOB_ID/result | jq '.'
```

### Example 3: Batch Processing with Status Check

```python
import requests
import time

# Submit batch
patient_ids = ["pat-1", "pat-2", "pat-3", "pat-4", "pat-5"]
job_ids = []

for pid in patient_ids:
    resp = requests.post("http://localhost:5001/audit", json={
        "patient_id": pid,
        "audit_type": "diabetes_management"
    })
    job_ids.append(resp.json()["job_id"])

print(f"Submitted {len(job_ids)} jobs")

# Wait for all to complete
results = {}
while len(results) < len(job_ids):
    for job_id in job_ids:
        if job_id in results:
            continue

        status = requests.get(f"http://localhost:5001/audit/{job_id}").json()
        if status["status"] == "completed":
            result = requests.get(f"http://localhost:5001/audit/{job_id}/result").json()
            results[job_id] = result
            print(f"✓ Job {job_id[:8]}... completed")
        elif status["status"] == "failed":
            results[job_id] = {"error": status["message"]}
            print(f"✗ Job {job_id[:8]}... failed")

    time.sleep(2)

print(f"\nAll {len(results)} jobs completed!")
```

---

## Scaling Workers

### Run Multiple Workers

Process jobs faster by running multiple workers:

```bash
# Terminal 1
celery -A aiorchestrator.celery_app worker --loglevel=info --concurrency=2

# Terminal 2
celery -A aiorchestrator.celery_app worker --loglevel=info --concurrency=2

# Now you have 4 concurrent workers
```

### Production Deployment

```bash
# Run as daemon with auto-restart
celery -A aiorchestrator.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=100 \
  --detach
```

---

## Monitoring

### View Queue in Real-Time

```bash
# Celery Flower (web-based monitoring)
pip install flower
celery -A aiorchestrator.celery_app flower

# Visit http://localhost:5555
```

### Check Redis Queue

```bash
# Connect to Redis
redis-cli

# View all keys
keys *

# Get queue length
llen celery

# View task by ID
get celery-task-meta-<job_id>
```

---

## Configuration

### Task Timeouts

Edit `aiorchestrator/celery_app.py`:

```python
celery_app.conf.update(
    task_time_limit=300,       # Hard limit: 5 minutes
    task_soft_time_limit=240,  # Soft limit: 4 minutes (warning)
)
```

### Retry Policy

Edit `aiorchestrator/tasks.py`:

```python
@celery_app.task(
    max_retries=3,            # Retry up to 3 times
    default_retry_delay=60,   # Wait 60 seconds between retries
)
```

### Result Expiration

Edit `aiorchestrator/celery_app.py`:

```python
celery_app.conf.update(
    result_expires=3600,  # Results expire after 1 hour
)
```

---

## Troubleshooting

### "Connection refused" on Redis

```bash
# Check if Redis is running
docker compose ps redis

# Restart Redis
docker compose restart redis

# Check logs
docker compose logs redis
```

### No workers available

```bash
# Check workers
celery -A aiorchestrator.celery_app inspect active

# Start a worker
celery -A aiorchestrator.celery_app worker --loglevel=info
```

### Jobs stuck in PENDING

```bash
# Purge all tasks
celery -A aiorchestrator.celery_app purge

# Restart workers
pkill -f "celery worker"
celery -A aiorchestrator.celery_app worker --loglevel=info
```

### View task errors

```bash
# View worker logs
celery -A aiorchestrator.celery_app events

# Or check Flower UI
celery -A aiorchestrator.celery_app flower
```

---

## Benefits of Queue System

✅ **Non-blocking**: API responds instantly with job ID
✅ **Scalable**: Add more workers to process faster
✅ **Reliable**: Failed jobs are retried automatically
✅ **Fair**: FIFO queue ensures fair processing
✅ **Trackable**: Monitor job status and queue stats
✅ **Production-ready**: Battle-tested Celery framework

---

## Next Steps

1. ✅ Queue system is set up
2. Start Redis: `docker compose up redis -d`
3. Start worker: `celery -A aiorchestrator.celery_app worker --loglevel=info`
4. Start API: `python main.py`
5. Submit jobs and track them!
