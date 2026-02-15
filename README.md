# MedAudit — Breast Cancer Screening Audit

**Automated breast cancer screening compliance auditing for Electronic Health Record systems.**

MedAudit runs guideline-based audits of patient EHR data (FHIR or mock) against **breast cancer screening** clinical guidelines (mammography, eligibility, follow-up, documentation). It uses RAG over a medical knowledge base (ChromaDB), an AI audit engine, and surfaces findings through a web dashboard for clinical review.

**Project focus:** Breast Cancer Screening Audit (guidelines in `docs/Medical_KB/Clinical_Guidelines/`).

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose v2](https://docs.docker.com/compose/install/)
  - On Ubuntu/Debian: `sudo apt install docker-compose-v2`

## Run MedAudit (default)

By default, only the **MedAudit** stack runs (PostgreSQL, Redis, backend, Celery worker, frontend, nginx):

```bash
git clone https://github.com/<owner>/MedAudit.git
cd MedAudit
cp .env.example .env   # optional: edit for JWT, OpenAI embeddings, etc.
docker compose up --build
```

- **App:** <http://localhost> (nginx → frontend + `/api` → backend)
- **Sign up** via the UI, then log in and create a **breast cancer screening audit job** (patient ID).

Optional platform/HAPI services (different app) are behind profiles and do not start by default:

```bash
docker compose --profile platform --profile hapi up --build
```

## Create first user (MedAudit)

Use the in-app **Sign up** flow at <http://localhost>, or call the backend auth API to register. Then use **New screening audit job** to queue an audit (EHR + RAG + AI report).

---

# Operations

## Development with Hot Reloading

The development setup automatically reloads when you make changes:

- **Backend changes**: Edit files in `platform/backend/` — Flask will
  reload automatically
- **Frontend changes**: Edit files in `platform/ui/src/` — Vite HMR
  updates the browser instantly

## Stopping the Application

```bash
# Stop containers
sudo docker compose down

# Stop and remove data volumes
sudo docker compose down -v
```

See `platform/README.md` for detailed documentation on migrations, CLI
commands, API endpoints, and production deployment.

---

# Architecture

**MedAudit (default `docker compose up`):**

- Web UI: http://localhost (port 80, nginx)
- API: http://localhost/api
- PostgreSQL: medaudit_db (internal); ChromaDB persisted in backend volume

**With `--profile platform`:** Web UI and API at http://localhost:8080; DB at localhost:5432.

<!-- TODO: Fill in some technical information -->

---

# Contributing

## Branching Strategy

### Main Branches

- **`main`** — Production-ready code
- **`develop`** — Integration branch for new features

### Feature Branches

- Frontend contributors: `feature/frontend/[feature-name]`
- Backend contributors: `feature/backend/[feature-name]`

## Workflow

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/frontend/your-feature-name
   # or
   git checkout -b feature/backend/your-feature-name
   ```

2. **Make Changes**
   - Frontend: Work in `/frontend` directory
   - Backend: Work in `/backend` directory

3. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: your descriptive commit message"
   git push origin feature/your-branch-name
   ```

4. **Create Pull Request**
   - Target branch: `develop`
   - Add reviewers
   - Ensure CI passes

5. **Merge Process**
   - PR → `develop` (after review)
   - `develop` → `main` (release-ready)

## Getting Started

1. Clone the repository
2. Choose your component (frontend/backend)
3. Follow component-specific setup instructions
4. Create your feature branch from `develop`

## Commit Convention
