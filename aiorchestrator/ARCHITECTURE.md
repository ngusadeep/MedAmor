# MedAudit Aiorchestrator – Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              MedAudit Aiorchestrator                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────────┐ │
│   │   Client     │─────▶│  Flask API   │─────▶│    Redis     │◀────▶│   Celery    │ │
│   │  (HTTP)      │      │  (main.py)   │      │   Broker     │      │   Worker    │ │
│   └──────────────┘      └──────────────┘      └──────────────┘      └──────┬──────┘ │
│         │                       │                        │                     │     │
│         │                       │                        │                     │     │
│         ▼                       ▼                        │                     ▼     │
│   ┌──────────────┐      ┌──────────────┐                │              ┌──────────┐ │
│   │ POST /audit  │      │ GET /audit/  │                │              │ LangGraph│ │
│   │ GET /health  │      │   <job_id>   │                │              │  Agent   │ │
│   └──────────────┘      └──────────────┘                │              └────┬─────┘ │
│                                                                              │       │
│   ┌──────────────────────────────────────────────────────────────────────────┼───┐  │
│   │                         LangGraph StateGraph                              │   │  │
│   │   ┌────────────┐    ┌─────────────┐    ┌────────────────┐                 │   │  │
│   │   │ fetch_fhir │───▶│retrieve_docs│───▶│ generate_report│─────────────────┘   │  │
│   │   └─────┬──────┘    └──────┬──────┘    └───────┬────────┘                     │  │
│   │         │                  │                   │                              │  │
│   └─────────┼──────────────────┼───────────────────┼──────────────────────────────┘  │
│             │                  │                   │                                  │
│             ▼                  ▼                   ▼                                  │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                      │
│   │ HAPI FHIR /     │  │ ChromaDB        │  │ Google Gemini   │                      │
│   │ Dummy Data      │  │ (Embeddings +   │  │ (ChatGoogle     │                      │
│   │ (fhir.py)       │  │  Guidelines)    │  │  GenerativeAI)  │                      │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘                      │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Diagram (Mermaid)

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        HTTP[HTTP Client]
    end

    subgraph API["Flask API (main.py)"]
        POST[POST /audit]
        GET_STATUS[GET /audit/&lt;job_id&gt;]
        GET_RESULT[GET /audit/&lt;job_id&gt;/result]
        QUEUE_STATS[GET /queue/stats]
        HEALTH[GET /health]
    end

    subgraph Queue["Task Queue"]
        Redis[(Redis Broker)]
        Celery[Celery Worker]
    end

    subgraph Agent["LangGraph Agent (agent.py)"]
        direction TB
        START([START]) --> FETCH[fetch_fhir]
        FETCH --> RETRIEVE[retrieve_docs]
        RETRIEVE --> GENERATE[generate_report]
        GENERATE --> END([END])
    end

    subgraph Data["Data Sources"]
        FHIR[HAPI FHIR Server]
        Chroma[(ChromaDB)]
        Gemini[Google Gemini API]
    end

    subgraph Modules["Internal Modules"]
        FHIR_MOD[fhir.py]
        VECTOR[vector_store.py]
    end

    HTTP --> POST
    HTTP --> GET_STATUS
    HTTP --> GET_RESULT
    HTTP --> QUEUE_STATS
    HTTP --> HEALTH

    POST --> Redis
    Redis --> Celery
    Celery --> Agent

    FETCH --> FHIR_MOD
    FHIR_MOD --> FHIR
    RETRIEVE --> VECTOR
    VECTOR --> Chroma
    GENERATE --> Gemini

    Celery --> Redis
```

---

## LangGraph Workflow Detail

```mermaid
stateDiagram-v2
    [*] --> fetch_fhir: patient_id, audit_type
    fetch_fhir --> retrieve_docs: fhir_data
    retrieve_docs --> generate_report: context (RAG chunks)
    generate_report --> [*]: report

    note right of fetch_fhir
        - HAPI FHIR $everything
        - Or dummy bundle if USE_DUMMY_FHIR=true
    end note

    note right of retrieve_docs
        - ChromaDB similarity_search
        - Google Embeddings (gemini-embedding-001)
    end note

    note right of generate_report
        - ChatGoogleGenerativeAI
        - Structured output (compliant, gaps, evidence)
    end note
```

---

## Directory Structure

```
aiorchestrator/
├── main.py                 # Flask app: HTTP API, Celery task dispatch
├── pyproject.toml
├── ARCHITECTURE.md         # This file
│
├── aiorchestrator/         # Python package
│   ├── __init__.py
│   ├── celery_app.py      # Celery config (Redis broker)
│   ├── tasks.py           # run_patient_audit Celery task
│   │
│   └── app/
│       ├── __init__.py
│       ├── agent.py       # LangGraph StateGraph (fetch_fhir → retrieve_docs → generate_report)
│       ├── fhir.py        # fetch_patient_bundle, format_patient_summary
│       └── vector_store.py # ChromaDB + Google Embeddings, ingest_guidelines
│
├── tests/
│   ├── test_fhir_client.py
│   ├── test_fhir_reader_adapter.py
│   ├── test_guidelines.py
│   ├── test_orchestrator.py
│   └── test_prompt_builder.py
│
├── ingest_guidelines.py    # CLI to load guidelines into ChromaDB
└── .env                    # GOOGLE_API_KEY, REDIS_URL, HAPI_FHIR_URL, USE_DUMMY_FHIR
```

---

## Data Flow

| Stage | Input | Output |
|-------|-------|--------|
| **POST /audit** | `{patient_id, audit_type}` | `{job_id}` (202 Accepted) |
| **Celery Task** | `patient_id, audit_type` | Queued → Worker |
| **fetch_fhir** | `patient_id` | `fhir_data` (FHIR Bundle) |
| **format_patient_summary** | `fhir_data` | Narrative string |
| **retrieve_docs** | `audit_type + patient_summary` | `context` (guideline chunks) |
| **generate_report** | `patient_summary, context, audit_type` | `report` (JSON: compliant, gaps, evidence) |
| **Task Result** | — | `{status, report, sources}` |

---

## External Dependencies

| Component | Purpose |
|-----------|---------|
| **Redis** | Celery message broker & result backend |
| **HAPI FHIR** | Patient data (or dummy if `USE_DUMMY_FHIR=true`) |
| **ChromaDB** | Vector store for clinical guidelines (local `./chroma_data`) |
| **Google Gemini** | LLM (gemini-2.0-flash-exp) + Embeddings (gemini-embedding-001) |
