# MedArmor

**Automated medical guideline compliance auditing for Electronic Health
Record systems.**

MedArmor monitors EHR data through FHIR interfaces and audits patient
records against clinical guidelines to identify cases where care protocols
may not have been followed. It converts complex FHIR bundles into
human-readable timelines, flags potential compliance gaps, and surfaces
findings through a web dashboard for clinical review.

<!-- TODO: Add a screenshot of the dashboard here -->
<!-- ![MedArmor Dashboard](docs/images/dashboard.png) -->

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and
  [Docker Compose v2](https://docs.docker.com/compose/install/)
  - On Ubuntu/Debian: `sudo apt install docker-compose-v2`

## 1. Point to your FHIR API

<!-- TODO: Add steps on specifying an FHIR URL to connect to -->
If you do not have a FHIR API server but wish to test, see the
instructions in [ehr/README.md](./ehr/README.md).

## 2. Start the application

```bash
git clone https://github.com/<owner>/MedAudit.git
cd MedAudit
sudo docker compose up --build
```

## 3. Create your first user

```bash
# Interactive (recommended)
sudo docker compose exec -it platform_web uv run platform-cli create-user

# Or non-interactive
sudo docker compose exec platform_web uv run platform-cli create-user \
  --username admin \
  --email admin@example.com \
  --password yourpassword \
  --admin
```

## 4. Open the dashboard

Navigate to <http://localhost:8080> and log in.

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

The system is made of these components:

- Web UI: http://localhost:8080
- API: http://localhost:8080/api
- API Database: localhost:5432

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
