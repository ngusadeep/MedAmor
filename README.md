# MedAudit

A monorepo containing frontend and backend components for medical audit system.

## Branching Strategy

### Main Branches
- **`main`** - Production-ready code
- **`develop`** - Integration branch for new features

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

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Format: `<type>[scope]: <description>`.

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation
- `style:` - Code style (formatting, no logic change)
- `refactor:` - Code refactoring
- `perf:` - Performance
- `test:` - Tests
- `chore:` - Maintenance, deps, tooling
- `build:` / `ci:` - Build or CI config

Scope examples: `feat(backend): add auth`, `fix(frontend): table sort`. See **docs/PROJECT_STANDARDS.md** for full conventions.