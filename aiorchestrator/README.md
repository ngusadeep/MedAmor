# AI Orchestrator - Medical Audit Engine

LangGraph-powered AI orchestrator that audits patient FHIR records against clinical guidelines using Google Gemini.

## Architecture

**Workflow**: `patient_id + audit_type` → Fetch FHIR → Retrieve Guidelines (RAG) → Gemini Audit → Structured Report

**Stack**:
- **LangGraph**: State machine orchestration
- **Google Gemini**: Medical reasoning LLM
- **ChromaDB**: Vector store for guideline retrieval (RAG)
- **HAPI FHIR**: Patient data source
- **Flask**: REST API

## Quick Start

### 1. Install Dependencies

```bash
cd aiorchestrator
uv sync
# or: pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

**Required**:
- `GOOGLE_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Optional**:
- `GEMINI_MODEL`: Model choice (default: `gemini-2.0-flash-exp`)
- `HAPI_FHIR_URL`: FHIR server URL (default: `http://localhost:9080/fhir`)
- `USE_DUMMY_FHIR`: Use dummy data if FHIR server unavailable (default: `false`)

### 3. Start HAPI FHIR Server

The orchestrator needs patient data from the EHR:

```bash
# From project root
docker compose up hapi_fhir hapi_db
```

Wait for FHIR server to be ready (~2-3 minutes):

```bash
curl http://localhost:9080/fhir/metadata
```

### 4. Upload Sample Patient Data

```bash
cd ../ehr
./upload_fhir.sh data/breast/fhir/
```

Get a patient ID:

```bash
curl -s "http://localhost:9080/fhir/Patient?_count=1" | jq -r '.entry[0].resource.id'
```

### 5. Ingest Medical Guidelines

Load the Medical Knowledge Base into ChromaDB:

```bash
cd ../aiorchestrator
python ingest_guidelines.py
```

This processes all markdown files in `docs/Medical_KB/` and creates embeddings.

**Output**:
```
Medical Knowledge Base: /path/to/docs/Medical_KB
ChromaDB Directory: ./chroma_data
Ingesting medical guidelines...
✓ Successfully ingested 342 text chunks
Vector store ready for RAG retrieval!
```

To reset and re-ingest:
```bash
python ingest_guidelines.py --force
```

### 6. Start the API

```bash
python main.py
# or: flask run
```

Server runs on `http://localhost:5000`

## API Usage

### POST /audit

Audit a patient against clinical guidelines.

**Request**:
```bash
curl -X POST http://localhost:5000/audit \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "26171",
    "audit_type": "hypertension_compliance"
  }'
```

**Response**:
```json
{
  "status": "success",
  "report": "{\"compliant\": false, \"gaps\": [...], \"evidence\": [...]}",
  "sources": ["guideline chunk 1", "guideline chunk 2", ...]
}
```

**Audit Report Structure**:
```json
{
  "compliant": false,
  "gaps": [
    "Blood pressure 142/88 exceeds target <130/80 mmHg",
    "No documentation of lifestyle modifications"
  ],
  "evidence": [
    {
      "guideline": "Hypertension Treatment Guidelines - BP Target",
      "violation": "Current BP 142/88 exceeds recommended threshold"
    }
  ]
}
```

**Audit Types**:
- `hypertension_compliance`
- `diabetes_management`
- `cardiology_compliance`
- `general` (default)

### GET /health

Health check endpoint.

```bash
curl http://localhost:5000/health
```

## Development

### Project Structure

```
aiorchestrator/
├── main.py                    # Flask API entrypoint
├── ingest_guidelines.py       # CLI to load Medical KB
├── .env.example               # Environment template
└── aiorchestrator/
    └── app/
        ├── agent.py           # LangGraph state machine
        ├── fhir.py            # FHIR client & formatting
        └── vector_store.py    # ChromaDB setup
```

### LangGraph Workflow

**State Schema** (`AuditState`):
```python
{
    "patient_id": str,       # Patient identifier
    "audit_type": str,       # Audit category
    "fhir_data": dict,       # FHIR Bundle from $everything
    "context": list[str],    # Retrieved guideline chunks (RAG)
    "report": str            # Final JSON audit report
}
```

**Node Flow**:
1. **fetch_fhir**: `GET /Patient/{id}/$everything` from HAPI FHIR
2. **retrieve_docs**: Semantic search on ChromaDB (top 5 guidelines)
3. **generate_report**: Gemini structured output (Pydantic schema)

### Testing Without FHIR Server

Set `USE_DUMMY_FHIR=true` in `.env` to use sample data:

```bash
USE_DUMMY_FHIR=true python main.py
```

### Updating Guidelines

After modifying files in `docs/Medical_KB/`:

```bash
python ingest_guidelines.py --force
```

## Troubleshooting

**"GOOGLE_API_KEY not found"**:
- Create `.env` from `.env.example`
- Add your API key from Google AI Studio

**"Failed to fetch FHIR data"**:
- Ensure HAPI FHIR is running: `docker compose ps`
- Check server: `curl http://localhost:9080/fhir/metadata`
- Upload patient data: `cd ehr && ./upload_fhir.sh data/breast/fhir/`

**"No documents found in vector store"**:
- Run: `python ingest_guidelines.py`
- Check Medical_KB path is correct in `.env`

**ChromaDB errors**:
- Delete `./chroma_data` and re-run `python ingest_guidelines.py`

## Production Deployment

1. Set `FLASK_ENV=production`
2. Use Gunicorn: `gunicorn -w 4 main:app`
3. Use `gemini-3-pro` for complex audits
4. Mount persistent ChromaDB volume
5. Configure proper FHIR authentication

## Model Selection

- **gemini-2.0-flash-exp**: Fast, cost-effective (default)
- **gemini-3-pro**: Advanced reasoning for complex cases

Set in `.env`:
```bash
GEMINI_MODEL=gemini-3-pro
```
