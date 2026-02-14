# MedAudit Demo UI

Interactive web interface for testing the AI Orchestrator breast cancer screening audit system.

## Features

- ✅ **Submit Patient Audits** - Enter patient ID and audit type
- ✅ **Real-time Job Tracking** - Watch audit progress with live status updates
- ✅ **Queue Statistics** - Monitor workers, active jobs, and queue depth
- ✅ **Demo Patient** - Quick-load Mrs. Justine Garnett's test case
- ✅ **Audit Results Display** - View compliance status, gaps, and evidence
- ✅ **BI-RADS Reference** - Quick lookup for follow-up timing guidelines

## Prerequisites

Before using the demo UI, ensure the following services are running:

### 1. Redis (Task Queue)
```bash
docker compose up redis -d
```

### 2. Celery Worker
```bash
cd aiorchestrator
./start_worker.sh
```

### 3. Flask API
```bash
cd aiorchestrator
uv run python main.py
```

The API should be running at `http://localhost:5001`

## Usage

### Option 1: Using a Web Server (Recommended)

**Using Python:**
```bash
cd audit-demo-ui
python3 -m http.server 8000
```

**Using Node.js:**
```bash
cd audit-demo-ui
npx serve
```

Then open: `http://localhost:8000`

### Option 2: Open Directly

Simply open `index.html` in your browser. Note: Some browsers may block CORS requests when opening files directly. Using a web server is recommended.

## How to Test

### Test 1: Demo Patient (Mrs. Justine Garnett)

1. Click the **"Load Demo"** button
2. This pre-fills the patient ID: `39b7de4b-abf2-d772-461e-193e503a035b`
3. Click **"Submit Audit"**
4. Watch the real-time status updates
5. Expected result: **✅ COMPLIANT** (surveillance within 6-12 months post-treatment)

**Patient Background:**
- Age 45, Stage IA breast cancer diagnosed 2023-07-23
- Treatment: Lumpectomy + 8 cycles chemotherapy (completed 2024-01-12)
- Surveillance mammography: 2024-12-10 (11 months post-treatment)
- Guideline: BI-RADS Category 6 requires surveillance within 6-12 months

### Test 2: Custom Patient

1. Enter any patient ID (must exist in FHIR server or use dummy data)
2. Select audit type
3. Click **"Submit Audit"**
4. View results

### Test 3: Queue System

1. Submit multiple audits rapidly
2. Watch the **Queue Status** panel update
3. Observe jobs moving through: Queued → Processing → Success

## UI Components

### Header
- **API Status Indicator**: Green = Connected, Red = Offline
- **Refresh Stats**: Manually refresh queue statistics

### Left Panel - Submit Audit
- **Patient ID**: Enter patient identifier
- **Audit Type**: Select from breast cancer screening, hypertension, diabetes, or general
- **Submit Button**: Queue the audit job
- **Results Section**: Displays job status and final audit report

### Right Panel - Stats & Reference
- **Queue Status**: Real-time worker and job counts
- **Recent Audits**: Last 5 submitted audits
- **BI-RADS Quick Ref**: Follow-up timing guidelines for Categories 0-6

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check API availability |
| `/audit` | POST | Submit new audit job |
| `/audit/{job_id}` | GET | Check job status |
| `/audit/{job_id}/result` | GET | Get completed audit result |
| `/queue/stats` | GET | Get queue statistics |

## Troubleshooting

### API Status Shows "Offline"

**Check if Flask API is running:**
```bash
curl http://localhost:5001/health
```

**Expected response:**
```json
{"status": "healthy"}
```

### No Workers Available

**Check Celery worker:**
```bash
cd aiorchestrator
./start_worker.sh
```

Look for output: `celery@hostname ready`

### Job Stays "Pending"

This means no worker is available to process the job.

**Solution:**
1. Ensure Redis is running: `docker ps | grep redis`
2. Ensure worker is running: Check terminal with `./start_worker.sh`
3. Check worker logs for errors

### CORS Errors

If opening `index.html` directly, use a web server instead:
```bash
python3 -m http.server 8000
```

### Audit Fails

**Check API logs:**
```bash
cd aiorchestrator
uv run python main.py
```

**Common issues:**
- Missing Google API key in `.env`
- Patient ID not found in FHIR server (set `USE_DUMMY_FHIR=true` for testing)
- Guidelines not ingested into ChromaDB

## Demo Workflow

```
User enters patient ID
    ↓
Click "Submit Audit"
    ↓
API queues job → Returns job_id
    ↓
UI polls /audit/{job_id} every 2s
    ↓
Worker picks up job
    ↓
Status: PENDING → PROCESSING → SUCCESS
    ↓
UI fetches final result
    ↓
Display audit report with compliance status
```

## Tips

- **Auto-refresh**: Queue stats refresh automatically every 5 seconds
- **Demo patient**: Use the "Load Demo" button to test with known-good data
- **Recent audits**: Track your testing history in the right panel
- **BI-RADS reference**: Use the quick reference to understand expected follow-up timings

## Next Steps

1. Test with the demo patient to verify the system works
2. Upload additional FHIR patient bundles to HAPI server
3. Create test cases for different BI-RADS categories
4. Experiment with different audit types

---

**Built for MedAudit MVP** - AI-powered breast cancer screening compliance audit system
