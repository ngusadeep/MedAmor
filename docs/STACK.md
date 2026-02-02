# MedAudit — Tech Stack & Tools

EHR AI platform stack. All listed libraries are installed and used as we build features.

---

## 1. Frontend (UI)

- **Framework:** React (Vite)
- **Theme / UI:** Shadcn (slate theme), Tailwind CSS
- **State:** Zustand
- **Charts:** Recharts, Shadcn/ui
- **HTTP:** Axios
- **Auth:** JWT (HTTP-only cookies via backend)
- **Forms:** react-hook-form, zod

**Pages / features:** Login, Patient Review Form, Historical Reports Table, Config (FHIR URL, emails, alerts).

Templates and blocks in the frontend can be reused and updated for these needs.

---

## 2. Backend API

- **Framework:** FastAPI
- **Validation:** Pydantic
- **Server:** Uvicorn (ASGI)
- **Auth:** JWT + HTTP-only cookies
- **Queue:** RabbitMQ (Celery AMQP)
- **Scheduling:** Celery Beat / APScheduler
- **HTTP client:** httpx
- **Containers:** Docker

**API:** Receive AI outputs, store in Postgres, serve UI, push jobs to queue.

---

## 3. Databases

| Role              | Technology        | Purpose                                              |
|-------------------|-------------------|------------------------------------------------------|
| Platform DB       | Postgres          | Users, Patients, Jobs, AI Findings, Config, Notifications |
| EHR (optional)    | HAPI FHIR / Postgres | EHR resources for retrieval and vectorization       |
| Vector DB         | Qdrant            | Embeddings of EHR and clinical notes                 |

**Embeddings (RAG):** ClinicalBERT (EHR text), small-embedding-GPT3 (structured / metadata).

---

## 4. AI / RAG Layer

- **Inference:** MedGemma-4B (multimodal, text + images) via Hugging Face Inference Endpoints
- **Orchestration:** LangChain, LangGraph
- **Indexing (optional):** LlamaIndex
- **Observability:** LangSmith

**RAG flow:** Query EHR + user input → vectorize (ClinicalBERT / small-embedding-GPT3) → Qdrant → MedGemma-4B → structured report (Job/Patient ID, Date, Urgency, Findings, Corrective Actions, Explainability) → API → DB → frontend.

---

## 5. Agent / Worker Layer

- **Queue:** RabbitMQ (Pika / aio-pika)
- **Tasks:** Celery
- **Role:** Poll queue, run AI review, push results to backend API
- **Deploy:** Python + Docker; optional scaling with Kubernetes

---

## 6. Deployment

- **MVP:** Docker + Docker Compose
- **Optional:** Kubernetes + Helm
- **Monitoring:** Prometheus + Grafana / ELK
- **Secrets:** Vault / K8s secrets / `.env`

**Containers (target):**

1. `platform-db` — Postgres  
2. `ehr-db` — Postgres HAPI (optional)  
3. `backend-api` — FastAPI + Uvicorn  
4. `frontend-ui` — React Vite + Shadcn (slate)  
5. `rabbitmq` — Message queue  
6. `vector-db` — Qdrant  
7. `agent-worker` — Python AI worker + MedGemma  

---

## 7. Installed Packages

| Layer            | Packages |
|------------------|----------|
| **Frontend**     | React, Vite, Tailwind, Zustand, Recharts, Shadcn/ui, Axios |
| **Backend**      | FastAPI, Pydantic, Uvicorn, SQLAlchemy, httpx, python-jose, passlib, python-multipart |
| **Queue / tasks**| Celery (AMQP), aio-pika |
| **Vector / RAG** | qdrant-client, langchain, langchain-community, langgraph, langchain-qdrant |
| **Observability**| langsmith |
| **Containers**   | Docker, Docker Compose |

Embedding models (ClinicalBERT, small-embedding-GPT3) and MedGemma are wired in when we implement the RAG and inference pipelines.
