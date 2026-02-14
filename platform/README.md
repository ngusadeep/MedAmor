# MedArmor

Medical audit web application: Flask backend, React/TypeScript frontend, PostgreSQL. Migrations and default admin user run automatically on startup (idempotent).

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Docker
- Docker Compose

**Tech stack:** Backend — Flask, SQLAlchemy, Alembic, uv. Frontend — React, TypeScript, Vite, Tailwind, shadcn/ui. Runtime — Nginx, Gunicorn (prod).

### Running the Application

**Clone the repository:**

```bash
git clone <repository-url>
cd <repo-root>
```

**Docker (full stack; recommended):**

```bash
docker compose up -d
```

Migrations and default admin are applied on first start. No manual setup.

**Backend (local):**

```bash
cd platform
uv sync
cp backend/.env.example backend/.env
# Edit .env (DB, etc.)
DATABASE_HOST=localhost uv run python -m backend.app
```

**Frontend (local):**

```bash
cd platform/ui
npm install
npm run dev
```

### Access

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8080
- **Default login:** `admin` / `admin@example.com` / `admin` (change in production)
