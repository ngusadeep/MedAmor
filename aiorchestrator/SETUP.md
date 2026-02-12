# AI Orchestrator Setup Guide

Complete step-by-step guide to get the AI orchestrator running with real FHIR data and medical guidelines.

## Prerequisites

- Python 3.12+
- Docker & Docker Compose (for HAPI FHIR server)
- Google API Key ([Get one here](https://makersuite.google.com/app/apikey))

## Step-by-Step Setup

### Step 1: Install Dependencies

```bash
cd aiorchestrator
uv sync
```

Or with pip:
```bash
pip install -e .
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:
```bash
GOOGLE_API_KEY=your_actual_api_key_here
```

**Important**: Keep `USE_DUMMY_FHIR=false` to use real patient data from HAPI FHIR.

### Step 3: Start HAPI FHIR Server

From the project root:

```bash
cd ..
docker compose up hapi_fhir hapi_db -d
```

Wait 2-3 minutes for the server to initialize. Check status:

```bash
# Should return FHIR CapabilityStatement
curl http://localhost:9080/fhir/metadata
```

### Step 4: Load Patient Data into EHR

```bash
cd ../ehr

# Upload sample patients
./upload_fhir.sh data/breast/fhir/
```

Verify patients were uploaded:

```bash
# List all patients
curl "http://localhost:9080/fhir/Patient?_count=5&_pretty=true"

# Get a patient ID (save this for testing)
curl -s "http://localhost:9080/fhir/Patient?_count=1" | jq -r '.entry[0].resource.id'
```

Example patient ID: `26171`

### Step 5: Ingest Medical Guidelines

Back to the orchestrator:

```bash
cd ../aiorchestrator

# Load Medical_KB into ChromaDB
python ingest_guidelines.py
```

Expected output:
```
Medical Knowledge Base: /path/to/MedAudit/docs/Medical_KB
ChromaDB Directory: ./chroma_data
Ingesting medical guidelines...
This may take a few minutes as documents are embedded...
✓ Successfully ingested 342 text chunks
Vector store ready for RAG retrieval!
```

**This step is crucial** - it creates the embeddings for the RAG system.

### Step 6: Test the Workflow

```bash
# Test with a real patient ID from Step 4
python test_workflow.py 26171 hypertension_compliance
```

Expected output:
```
Testing MedAudit Workflow
Patient ID: 26171
Audit Type: hypertension_compliance
------------------------------------------------------------

1. Building LangGraph workflow...
   ✓ Graph compiled

2. Executing audit workflow...
   → Fetching FHIR data...
   → Retrieving relevant guidelines...
   → Generating audit report with Gemini...
   ✓ Workflow complete

3. Audit Results:
------------------------------------------------------------

Compliance Status: ✗ NON-COMPLIANT

Identified Gaps (2):
  1. Blood pressure 142/88 exceeds target <130/80 mmHg
  2. No documentation of lifestyle modifications

Evidence (2):
  1. Guideline: Hypertension Treatment Guidelines
     Violation: Current BP exceeds recommended threshold
  ...
```

### Step 7: Start the API Server

```bash
python main.py
```

Server starts on `http://localhost:5000`

### Step 8: Test the API

In another terminal:

```bash
curl -X POST http://localhost:5000/audit \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "26171",
    "audit_type": "hypertension_compliance"
  }'
```

## Verification Checklist

- [ ] HAPI FHIR server is running (`curl http://localhost:9080/fhir/metadata`)
- [ ] Patient data is loaded (check with `curl http://localhost:9080/fhir/Patient`)
- [ ] ChromaDB has guidelines (`ls -la chroma_data/`)
- [ ] Google API key is set in `.env`
- [ ] Test workflow runs successfully
- [ ] API server responds to `/health` and `/audit`

## Common Issues

### "GOOGLE_API_KEY not found"
- Make sure `.env` file exists and contains `GOOGLE_API_KEY=...`
- Load it: `source .env` (bash) or just restart the Python process

### "Failed to fetch FHIR data"
- Check HAPI FHIR: `docker compose ps` (should show hapi_fhir as "Up")
- Check logs: `docker compose logs hapi_fhir`
- Try restarting: `docker compose restart hapi_fhir`

### "No patient found with ID X"
- List available patients: `curl http://localhost:9080/fhir/Patient?_count=10`
- Re-upload data: `cd ehr && ./upload_fhir.sh data/breast/fhir/`

### "No documents found in vector store"
- Run ingestion: `python ingest_guidelines.py`
- Check path: Verify `docs/Medical_KB/` exists relative to project root
- Force re-ingest: `python ingest_guidelines.py --force`

### ChromaDB persistence issues
- Delete and recreate: `rm -rf chroma_data && python ingest_guidelines.py`

## Development Tips

### Use Dummy Data for Frontend Testing

While developing the frontend without FHIR server:

```bash
# In .env
USE_DUMMY_FHIR=true
```

Then run normally:
```bash
python main.py
```

### Check What's in ChromaDB

```python
from aiorchestrator.app.vector_store import get_vector_store

vs = get_vector_store()
results = vs.similarity_search("hypertension treatment", k=3)
for doc in results:
    print(doc.page_content[:200])
    print(doc.metadata)
    print("---")
```

### Monitor LangGraph Execution

Add debug logging in `agent.py`:

```python
def fetch_fhir(state: AuditState) -> dict:
    print(f"DEBUG: Fetching FHIR for patient {state['patient_id']}")
    ...
```

## Next Steps

1. **Integrate with Platform**: Connect the orchestrator to the main web app
2. **Add More Audit Types**: Create specialized prompts for different specialties
3. **Improve RAG**: Fine-tune retrieval parameters (k, chunk size)
4. **Add Caching**: Cache frequently audited patients
5. **Production Deployment**: Use Gunicorn, proper logging, monitoring

## Complete Workflow Summary

```
User → POST /audit {patient_id, audit_type}
         ↓
    Flask API (main.py)
         ↓
    LangGraph (agent.py)
         ↓
    ┌──────────────────────────────┐
    │ fetch_fhir                   │
    │ → HAPI FHIR: Patient/$everything
    │ → Returns: FHIR Bundle       │
    └──────────────────────────────┘
         ↓
    ┌──────────────────────────────┐
    │ retrieve_docs                │
    │ → ChromaDB semantic search   │
    │ → Returns: Top 5 guidelines  │
    └──────────────────────────────┘
         ↓
    ┌──────────────────────────────┐
    │ generate_report              │
    │ → Google Gemini              │
    │ → Returns: Structured JSON   │
    └──────────────────────────────┘
         ↓
    Response: {compliant, gaps, evidence}
```

You're all set! 🎉
