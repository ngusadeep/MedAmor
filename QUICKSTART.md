# MedAudit - Quick Start Guide

**TL;DR:** Get the breast cancer screening audit system running in 5 minutes.

## Prerequisites
- Python 3.12+
- Docker
- Google API Key → https://aistudio.google.com/app/apikey

## Setup (One-time)

### 1. Configure API Key
```bash
cd aiorchestrator
# Edit .env and add your Google API key:
# GOOGLE_API_KEY=your_key_here
```

### 2. Install Dependencies
```bash
cd aiorchestrator
uv sync
```

### 3. Ingest Guidelines (Optional - already done if ChromaDB exists)
```bash
cd aiorchestrator
uv run python -c "from aiorchestrator.app.vector_store import ingest_medical_kb; ingest_medical_kb('../docs/Medical_KB')"
```

## Running the System

Open **4 terminals** and run these commands:

### Terminal 1: Redis
```bash
docker compose up redis -d
```

### Terminal 2: Celery Worker
```bash
cd aiorchestrator
./start_worker.sh
```
Wait for: `celery@hostname ready.`

### Terminal 3: Flask API
```bash
cd aiorchestrator
uv run python main.py
```
Wait for: `Running on http://127.0.0.1:5001`

### Terminal 4: Demo UI
```bash
cd audit-demo-ui
python3 -m http.server 8000
```

## Test It

1. Open: **http://localhost:8000**
2. Click **"Load Demo"**
3. Click **"Submit Audit"**
4. Watch it process → See result: **✅ COMPLIANT**

## Stop Everything

```bash
docker compose down redis  # Terminal 1
# Ctrl+C in Terminals 2, 3, 4
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| API Offline | Restart Terminal 3 (Flask API) |
| Job stays Pending | Check Terminal 2 - worker must be running |
| No results shown | Restart Flask API after code changes |

**Full docs:** See `SETUP_GUIDE.md`
