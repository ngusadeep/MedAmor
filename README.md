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

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Testing
- `chore:` - Maintenance



## Platform Setup

The platform provides a web application with a Flask backend, React frontend, and PostgreSQL database.

### Prerequisites

- Docker and Docker Compose v2 (**get v2**)
  - `sudo apt install docker-compose-v2`
- (Optional) Node.js 20+ and Python 3.11+ for local development
  - Find commands to install nvm then run `nvm install node`

### Quick Start

```bash
# Build and start all containers0
sudo docker compose up --build

# The application will be available at:
# - Web UI: http://localhost:8080
# - API: http://localhost:8080/api
# - Database: localhost:5432
```

### Create Your First User

```bash
# Interactive mode (preferred to keep passwords secure)
sudo docker compose exec -it platform_web uv run platform-cli create-user

# Or non-interactive
sudo docker compose exec platform_web uv run platform-cli create-user \
  --username admin \
  --email admin@example.com \
  --password yourpassword \
  --admin
```

### Development with Hot Reloading

The development setup automatically reloads when you make changes:

- **Backend changes**: Edit files in `platform/backend/` - Flask will reload automatically
- **Frontend changes**: Edit files in `platform/ui/src/` - Vite HMR updates the browser instantly


### Stopping the Application

```bash
# Stop containers
sudo docker compose down

# Stop and remove data volumes
sudo docker compose down -v
```

See `platform/README.md` for detailed documentation on migrations, CLI commands, API endpoints, and production deployment.
