# Project: MedAudit Backend (Flask + LangGraph + Gemini)

**Role:** Backend API for a medical audit orchestrator.
**Framework:** Flask (Python 3.12+).
**LLM Provider:** Google Gemini (via latest langchain-google-genai).

## 1. API Endpoint
- **POST /audit**
  - **Payload:** `{ "patient_id": "123", "audit_type": "cardiology_compliance" }`
  - **Response:** `{ "status": "success", "report": "...", "sources": [...] }`

## 2. Core Logic (LangGraph)
Create a `StateGraph` in `app/agent.py` using latest syntax (e.g., `addNode` shorthand, `MessagesAnnotation`).
- **State Schema:** TypedDict with `Annotation` (`patient_id`, `fhir_data`, `context`, `report`).
- **Nodes:**
  1. `fetch_fhir`: Fetch patient resources from HAPI FHIR public server.(CAN BE DUMMY)
  2. `retrieve_docs`: Vector search on ChromaDB (latest client config) using Google Embeddings.
  3. `generate_report`: Call Gemini to audit patient data against retrieved docs.

## 3. Tech Stack Requirements
- **LLM:** `ChatGoogleGenerativeAI` (package: `langchain-google-genai` latest).
  - Model: `gemini-3-pro` (Best reasoning) or `gemini-2.0-flash-exp` (Fastest).[web:17][web:24]
- **Embeddings:** `GoogleGenerativeAIEmbeddings`.
  - Model: `models/embedding-001`.
- **Vector Store:** ChromaDB (latest, with cloud-optional client auth).[web:4]
- **Orchestration:** LangGraph (latest, with interrupt handling).[web:3]
- **FHIR:** `fhirpy` (latest async/sync client).[web:5]

## 4. Specific Implementation Details
- **Environment:** Load `GOOGLE_API_KEY` from `.env`.
- **FHIR Processing:**
  - Helper `format_patient_summary(fhir_bundle)`: Convert JSON to narrative string for token efficiency.
- **Prompt:**
  - "You are an expert Medical Auditor. Use provided Clinical Guidelines to audit Patient History. Output strict JSON: {{\"compliant\": boolean, \"gaps\": [string], \"evidence\": [{\"guideline\": string, \"violation\": string}]}}."
