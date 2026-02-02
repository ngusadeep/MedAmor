# MedAudit — Project Standards

Project structure, naming, and conventions for the MedAudit monorepo. Cursor rules in `.cursor/rules/` reference this document.

---

## 1. Repository layout

```
MedAudit/
├── .cursor/
│   └── rules/              # Cursor AI rules (conventional-commits, fastapi-expert, project-standards)
├── backend/                 # FastAPI API, jobs, RAG, MedGemma, Celery
│   ├── app/                 # (recommended) routers, schemas, services, core
│   ├── main.py
│   ├── pyproject.toml
│   └── .env.example
├── frontend/                # React + Vite + shadcn
│   ├── src/
│   │   ├── app/             # Pages (dashboard, auth, audits, etc.)
│   │   ├── components/      # Shared UI, layouts, ui/
│   │   ├── config/          # Routes, API base URL
│   │   └── lib/, hooks/, types/, utils/
│   ├── package.json
│   └── .env.example
├── docs/
│   ├── PROJECT_PLAN.md      # Phased plan, decisions, EHR format, Kaggle
│   ├── PROJECT_STANDARDS.md # This file
│   └── Medical_KB/          # RAG knowledge base (Documentation, SOPs, User_Manuals, FAQs)
├── EHR-DATA_*/              # Sample EHR exports per patient (.txt timeline)
├── README.md
└── LICENSE
```

- **backend**: API, auth (JWT), jobs, audit engine, RAG, MedGemma (Hugging Face Inference), Celery + Redis.
- **frontend**: Login → dashboard (audits table) → manual review form → audit detail; calls backend API.
- **docs**: Plan, standards, and Medical_KB markdown for RAG indexing.
- **EHR-DATA_***: One folder per patient; mock API serves these `.txt` files by patient_id / export_type.

---

## 2. Branching and workflow

- **main** — Production-ready.
- **develop** — Integration for features.
- **Feature branches** — `feature/frontend/<name>` or `feature/backend/<name>` from `develop`.
- **PRs** target `develop`; after review, merge to `develop`; release from `develop` to `main`.

---

## 3. Git commits

All commits MUST follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

- **Format**: `<type>[optional scope]: <description>` plus optional body/footer.
- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, `revert`.
- **Scope**: e.g. `backend`, `frontend`, `auth`, `api`.
- **Description**: imperative, concise (e.g. "add JWT login", not "added JWT login").
- **Breaking changes**: footer `BREAKING CHANGE: ...` or `!` after type/scope (e.g. `feat(api)!: ...`).

Examples: `feat(backend): add audit jobs API`, `fix(frontend): audit table sort`, `docs: update PROJECT_PLAN`.

---

## 4. Naming conventions

| Layer    | Convention        | Example |
|----------|-------------------|--------|
| Backend files/dirs | lowercase, underscores | `audit_reports.py`, `user_routes.py`, `schemas/` |
| Backend identifiers | snake_case | `is_active`, `has_permission`, `audit_report_id` |
| Frontend components/pages | PascalCase | `AuditTable.tsx`, `ManualReviewForm.tsx` |
| Frontend locals/params | camelCase | `auditList`, `patientId` |
| API routes | kebab-case or snake_case | `/audit-reports/`, `/auth/login` |
| Env vars | UPPER_SNAKE; backend `BACKEND_*` or `*`, frontend `VITE_*` | `DATABASE_URL`, `VITE_API_URL` |

---

## 5. Backend (FastAPI) standards

- **Python**: 3.12+; type hints on all public functions; Pydantic v2 for request/response and config.
- **Structure**: Routers in `routers/` (or `app/routers/`), schemas in `schemas/`, business logic in `services/` or `core/`; keep route handlers thin.
- **Async**: Use `async def` for I/O (DB, HTTP); avoid blocking calls in request path.
- **Lifespan**: Use lifespan context manager for startup/shutdown; avoid deprecated `on_event`.
- **Errors**: `HTTPException` for expected failures; middleware for logging and unhandled errors.
- **Config**: Pydantic `BaseSettings` from env; document in `backend/.env.example` (no secrets in repo).

See `.cursor/rules/fastapi-expert.mdc` for detailed FastAPI/Python guidance when editing `backend/**/*.py`.

---

## 6. Frontend standards

- **Stack**: React, TypeScript, Vite, shadcn/ui; routing via `src/config/routes.tsx`.
- **Pages**: Under `src/app/<feature>/page.tsx`; reuse components from `src/components/`.
- **API**: Centralized base URL (e.g. `VITE_API_URL`); use fetch or a small client; send JWT in `Authorization` when required.
- **State**: Prefer local state and server data; use context or query lib only where needed.

---

## 7. API contract (audit)

- **Auth**: JWT in `Authorization: Bearer <token>`; login returns token; protected routes validate it.
- **Audit payload** (response): `job_id`, `patient_id`, `status` (NO_FINDINGS | FINDING_PRESENT), `executive_summary`, `findings[]` (category, description, responsible_doctor, urgency), `evidence[]` (kb_source, ehr_snippet, image_ref), `corrective_actions[]`, `risk_level`, `next_audit_date` (optional).

---

## 8. Documentation

- **PROJECT_PLAN.md**: Phases, decisions, EHR format, Kaggle submission; update when scope or decisions change.
- **Medical_KB**: Add or edit markdown under Documentation, SOPs, User_Manuals, FAQs; re-index for RAG when content changes.
- **README.md**: Getting started, branch strategy, commit convention (link to Conventional Commits and this doc).
- **.env.example**: List all env vars with short descriptions; no real secrets.

---

## 9. Checklist for new work

- [ ] Branch from `develop` with `feature/frontend/...` or `feature/backend/...`.
- [ ] Commits use Conventional Commits (`feat:`, `fix:`, etc.).
- [ ] Backend: type hints, Pydantic, async where appropriate; see fastapi-expert rule.
- [ ] Frontend: TypeScript; use existing routes and components where possible.
- [ ] Env and config documented in `.env.example` if new vars added.
- [ ] Docs (PROJECT_PLAN, Medical_KB, or this file) updated if behavior or structure changes.
