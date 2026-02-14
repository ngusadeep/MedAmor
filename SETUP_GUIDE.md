# MedAudit AI Orchestrator - Setup & Usage Guide

Complete guide for running the MedAudit breast cancer screening audit system with the interactive demo UI.

## Table of Contents
- [System Overview](#system-overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Running the System](#running-the-system)
- [Testing with Demo UI](#testing-with-demo-ui)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)

---

## System Overview

MedAudit is an AI-powered medical audit orchestrator that:
- ✅ Fetches patient data from FHIR EHR systems
- ✅ Retrieves relevant clinical guidelines using RAG (Retrieval Augmented Generation)
- ✅ Analyzes compliance using Google Gemini AI
- ✅ Processes multiple audits concurrently using Celery task queue
- ✅ Provides real-time audit status tracking via REST API

**Current MVP Focus:** Breast cancer screening compliance audits (BI-RADS follow-up timing)

---

## Prerequisites

### Required Software

1. **Python 3.12+**
   ```bash
   python3 --version
   ```

2. **UV Package Manager** (for Python dependency management)
   ```bash
   # Install UV if needed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Docker & Docker Compose** (for Redis)
   ```bash
   docker --version
   docker compose version
   ```

4. **Google API Key** (for Gemini AI)
   - Get your key from: https://aistudio.google.com/app/apikey
   - You'll need this for the `.env` file

### System Requirements
- macOS, Linux, or Windows (WSL recommended for Windows)
- At least 2GB free RAM
- Internet connection (for Google AI API)

---

## Initial Setup

### 1. Configure Environment Variables

Create or verify the `.env` file in the `aiorchestrator` directory:

```bash
cd /Users/sakib/Desktop/Factoryze/medgemma/MedAudit/aiorchestrator
```

Ensure `.env` contains:
```bash
# Google AI Configuration
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# FHIR Server Configuration
HAPI_FHIR_URL=http://localhost:9080/fhir
USE_DUMMY_FHIR=true

# Vector Store Configuration
CHROMA_PERSIST_DIR=./chroma_data
MEDICAL_KB_PATH=../docs/Medical_KB

# Task Queue Configuration
REDIS_URL=redis://localhost:6379/0

# Flask API Configuration
FLASK_RUN_PORT=5001
```

**Important:** Replace `your_api_key_here` with your actual Google API key.

### 2. Install Python Dependencies

```bash
cd aiorchestrator
uv sync
```

This installs all required packages:
- Flask + CORS (REST API)
- LangGraph (AI orchestration)
- Celery + Redis (task queue)
- ChromaDB (vector store)
- Google Gemini (LLM & embeddings)

### 3. Ingest Clinical Guidelines (One-time)

If you haven't already ingested the breast cancer guidelines:

```bash
cd aiorchestrator
uv run python -c "
from aiorchestrator.app.vector_store import ingest_medical_kb
ingest_medical_kb('../docs/Medical_KB')
print('✓ Guidelines ingested successfully')
"
```

You should see output like:
```
Ingesting documents from ../docs/Medical_KB...
Processing Clinical_Guidelines/breast_cancer_screening_guidelines.md
Loaded 1 documents
Split into 13 chunks
✓ 13 documents ingested into ChromaDB
✓ Guidelines ingested successfully
```

---

## Running the System

The system requires **4 services** to run concurrently. Open 4 terminal windows:

### Terminal 1: Start Redis (Task Queue)

```bash
cd /Users/sakib/Desktop/Factoryze/medgemma/MedAudit
docker compose up redis -d
```

**Verify it's running:**
```bash
docker ps | grep redis
```

Expected output:
```
CONTAINER ID   IMAGE              STATUS                    PORTS
f10dea3c3abf   redis:7-alpine     Up 5 minutes (healthy)   0.0.0.0:6379->6379/tcp
```

### Terminal 2: Start Celery Worker (Job Processor)

```bash
cd /Users/sakib/Desktop/Factoryze/medgemma/MedAudit/aiorchestrator
./start_worker.sh
```

**Wait for this message:**
```
Starting Celery Worker for MedAudit...
========================================
ℹ Skipping Redis check (redis-cli not installed)
  Ensure Redis is running: docker compose up redis -d

Starting worker with concurrency=2...
Press Ctrl+C to stop

 -------------- celery@Nazmuss-MacBook-Pro.local v5.x.x
---- **** -----
--- * ***  * -- Darwin-24.2.0-arm64
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         medaudit_orchestrator:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 1 (solo)
-- ******* ---- .> task events: OFF
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . aiorchestrator.tasks.run_patient_audit

[INFO/MainProcess] Connected to redis://localhost:6379/0
[INFO/MainProcess] celery@Nazmuss-MacBook-Pro.local ready.
```

**✅ Keep this terminal open** - you'll see audit jobs being processed here.

### Terminal 3: Start Flask API (Backend)

```bash
cd /Users/sakib/Desktop/Factoryze/medgemma/MedAudit/aiorchestrator
uv run python main.py
```

**Wait for this message:**
```
 * Serving Flask app 'main'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5001
 * Running on http://192.168.x.x:5001
Press CTRL+C to quit
```

**Verify it's working:**
```bash
# In a new terminal
curl http://localhost:5001/health
```

Expected: `{"status":"ok"}`

### Terminal 4: Start Demo UI (Frontend)

```bash
cd /Users/sakib/Desktop/Factoryze/medgemma/MedAudit/audit-demo-ui
python3 -m http.server 8000
```

Expected output:
```
Serving HTTP on :: port 8000 (http://[::]:8000/) ...
```

---

## Testing with Demo UI

### 1. Open the Demo Interface

Navigate to: **http://localhost:8000**

You should see:
- ✅ **API Status: Connected** (green indicator)
- Queue status showing 1 worker available
- Patient audit submission form

### 2. Run a Test Audit

**Option A: Use Demo Patient (Recommended)**

1. Click the **"Load Demo"** button
2. This auto-fills:
   - **Patient ID:** `39b7de4b-abf2-d772-461e-193e503a035b`
   - **Audit Type:** `breast_cancer_screening`
3. Click **"Submit Audit"**
4. Watch the real-time progress:
   - ⏳ Queued (yellow)
   - 🔄 Processing (blue)
   - ✅ Completed (green)
5. View the audit report showing compliance status

**Expected Result:**
```
✅ COMPLIANT

Patient: 39b7de4b-abf2-d772-461e-193e503a035b
Audit Type: Breast Cancer Screening

Evidence:
- Guideline: BI-RADS Category 6 requires surveillance every 6-12 months
- Finding: Surveillance performed 11 months post-treatment (within guideline)
```

**Option B: Custom Patient**

1. Enter any patient ID
2. Select audit type
3. Submit and view results

### 3. Monitor the System

**In Terminal 2 (Celery Worker):**
Watch for processing logs:
```
[INFO/MainProcess] Task aiorchestrator.tasks.run_patient_audit[abc-123] received
[INFO/ForkPoolWorker-1] Starting audit for patient: 39b7de4b...
[INFO/ForkPoolWorker-1] Task aiorchestrator.tasks.run_patient_audit[abc-123] succeeded
```

**In the Demo UI:**
- **Queue Status Panel:** Shows active workers and job counts
- **Recent Audits:** Tracks your submission history
- **Results Section:** Displays full audit reports with evidence

---

## Troubleshooting

### Issue 1: API Status Shows "Offline"

**Symptoms:** Red indicator in UI, cannot submit audits

**Solutions:**
1. Check Flask API is running on port 5001:
   ```bash
   curl http://localhost:5001/health
   ```
2. Check browser console for CORS errors (F12 → Console)
3. Restart Flask API:
   ```bash
   cd aiorchestrator
   uv run python main.py
   ```

### Issue 2: Jobs Stay in "Pending" Forever

**Symptoms:** Audit submitted but never processes

**Solutions:**
1. **Check if Celery worker is running:**
   ```bash
   ps aux | grep celery
   ```
   If nothing shows, worker is not running. Start it:
   ```bash
   cd aiorchestrator
   ./start_worker.sh
   ```

2. **Check if Redis is running:**
   ```bash
   docker ps | grep redis
   ```
   If not running:
   ```bash
   docker compose up redis -d
   ```

3. **Check worker logs** (Terminal 2) for errors

### Issue 3: "No Workers Available"

**Symptoms:** Queue stats show 0 workers

**Solution:**
Worker crashed or was never started. Check Terminal 2 for error messages, then restart:
```bash
cd aiorchestrator
./start_worker.sh
```

### Issue 4: Audit Results Don't Appear

**Symptoms:** Status changes to "Completed" but no report displays

**Solutions:**
1. **Check browser console** (F12) for JavaScript errors
2. **Restart Flask API** to apply latest code changes:
   ```bash
   cd aiorchestrator
   uv run python main.py
   ```
3. **Clear browser cache** and refresh page

### Issue 5: "Failed to Fetch FHIR Data"

**Symptoms:** Audit fails with FHIR error

**Solutions:**
1. **Use dummy data for testing:**
   In `.env`, set:
   ```bash
   USE_DUMMY_FHIR=true
   ```
2. **If using real HAPI FHIR server:**
   - Ensure HAPI server is running on port 9080
   - Check patient ID exists in the FHIR server
   - Verify `HAPI_FHIR_URL` in `.env`

### Issue 6: "Invalid API Key" or Gemini Errors

**Symptoms:** Audit fails during LLM processing

**Solutions:**
1. **Verify Google API key:**
   ```bash
   cd aiorchestrator
   grep GOOGLE_API_KEY .env
   ```
2. **Test API key:**
   ```bash
   curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_API_KEY"
   ```
3. **Check quota limits** at https://aistudio.google.com/

### Issue 7: Port Already in Use

**Symptoms:** `Address already in use` error when starting services

**Solutions:**

**For Flask API (port 5001):**
```bash
# Find and kill process
lsof -ti:5001 | xargs kill -9
```

**For Demo UI (port 8000):**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

**For Redis (port 6379):**
```bash
docker compose down redis
docker compose up redis -d
```

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Demo UI (Port 8000)                   │
│                    Interactive Web Interface                 │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Flask API (Port 5001)                      │
│              REST endpoints + CORS enabled                   │
│   /audit (POST) | /audit/{id} (GET) | /queue/stats (GET)   │
└────────────────────────┬────────────────────────────────────┘
                         │ Celery Tasks
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                 Redis Queue (Port 6379)                      │
│                    Task Broker + Backend                     │
└────────────────────────┬────────────────────────────────────┘
                         │ Workers Poll
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Celery Worker (solo pool)                 │
│                  Processes audit jobs async                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          LangGraph AI Orchestrator                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ Fetch FHIR │→│ Retrieve   │→│ Generate   │     │  │
│  │  │    Data    │  │ Guidelines │  │   Report   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  │         ↓              ↓                ↓            │  │
│  │    HAPI FHIR      ChromaDB        Gemini AI         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User submits audit** → Flask API queues job → Returns job ID
2. **Celery worker picks up job** → Executes LangGraph workflow:
   - **Node 1:** Fetch patient bundle from FHIR server
   - **Node 2:** RAG search in ChromaDB for relevant guidelines
   - **Node 3:** Gemini analyzes compliance and generates structured report
3. **Result stored in Redis** → Frontend polls for status → Displays report

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | HTML + Tailwind CSS + Vanilla JS | Interactive demo UI |
| **API** | Flask + Flask-CORS | REST endpoints |
| **Task Queue** | Celery + Redis | Async job processing |
| **Orchestration** | LangGraph | AI workflow state machine |
| **LLM** | Google Gemini 2.5 Flash | Compliance analysis |
| **Embeddings** | Google Gemini Embedding | Semantic search |
| **Vector Store** | ChromaDB | RAG guideline retrieval |
| **Data Format** | FHIR R4 | Healthcare data standard |
| **EHR Server** | HAPI FHIR (optional) | Patient data source |

---

## Quick Reference

### Start All Services (One-Liner per Terminal)

```bash
# Terminal 1 - Redis
docker compose up redis -d && docker logs -f medaudit_redis

# Terminal 2 - Celery Worker
cd aiorchestrator && ./start_worker.sh

# Terminal 3 - Flask API
cd aiorchestrator && uv run python main.py

# Terminal 4 - Demo UI
cd audit-demo-ui && python3 -m http.server 8000
```

### Stop All Services

```bash
# Stop Redis
docker compose down redis

# Stop Celery Worker (Ctrl+C in Terminal 2)

# Stop Flask API (Ctrl+C in Terminal 3)

# Stop Demo UI (Ctrl+C in Terminal 4)
```

### Health Checks

```bash
# Check Redis
docker ps | grep redis

# Check Celery worker
ps aux | grep celery

# Check Flask API
curl http://localhost:5001/health

# Check Demo UI
curl http://localhost:8000
```

### Useful Commands

```bash
# View worker logs in real-time
cd aiorchestrator && ./start_worker.sh

# Monitor Redis queue
docker exec -it medaudit_redis redis-cli LLEN celery

# Test API manually
curl -X POST http://localhost:5001/audit \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "test-123", "audit_type": "breast_cancer_screening"}'

# Check queue stats
curl http://localhost:5001/queue/stats | python3 -m json.tool
```

---

## Demo Patient Details

**Mrs. Justine Garnett**
- **Patient ID:** `39b7de4b-abf2-d772-461e-193e503a035b`
- **Age:** 45 years old
- **Diagnosis:** Stage IA invasive ductal carcinoma (2023-07-23)
- **Treatment:**
  - Lumpectomy (2023-08-05)
  - 8 cycles chemotherapy (completed 2024-01-12)
- **Surveillance:** Bilateral mammography (2024-12-10)
- **BI-RADS Category:** 6 (Known biopsy-proven malignancy)
- **Expected Result:** ✅ COMPLIANT (11 months post-treatment, within 6-12 month guideline)

---

## Next Steps

1. ✅ **Test with demo patient** to verify system works end-to-end
2. 📊 **Add more guidelines** to `docs/Medical_KB/` and re-ingest
3. 👥 **Upload patient data** to HAPI FHIR server and set `USE_DUMMY_FHIR=false`
4. 🧪 **Create test cases** for different BI-RADS categories (0-5)
5. 🔧 **Customize audit types** by modifying LangGraph prompts
6. 🚀 **Deploy to production** (use Gunicorn for Flask, multiple Celery workers)

---

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review worker logs (Terminal 2) for error messages
- Inspect browser console (F12) for frontend errors
- Verify all services are running with health checks

**Built with Claude Code** for MedAudit breast cancer screening compliance MVP.
