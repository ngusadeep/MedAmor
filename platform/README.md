# MedArmor

A medical audit web application built with Flask, React, TypeScript, and PostgreSQL.

## Project Structure

```
platform/
├── backend/                 # Flask backend
│   ├── __init__.py
│   ├── app.py              # Flask application factory
│   ├── startup.py          # Automated startup: default user (idempotent)
│   ├── cli.py              # CLI commands for user management
│   ├── config.py           # Configuration loader
│   ├── database.py         # Database setup
│   ├── models.py           # SQLAlchemy models
│   ├── routes.py           # API routes
│   └── migrations/         # Alembic migrations
│       ├── env.py
│       ├── script.py.mako
│       └── versions/       # Migration files
├── ui/                     # React frontend
│   ├── src/
│   │   ├── components/ui/  # shadcn components
│   │   ├── pages/          # Page components
│   │   ├── lib/            # Utilities
│   │   └── hooks/          # Custom React hooks
│   ├── package.json
│   └── vite.config.ts
├── config.toml             # Application configuration
├── alembic.ini             # Alembic configuration
├── nginx.conf              # Nginx config (development)
├── nginx.prod.conf         # Nginx config (production)
├── Dockerfile              # Docker build file
├── pyproject.toml          # Python project configuration
└── start.sh                # Container startup script
```

## Automated Startup

On every container start (`platform_web`), the following run **automatically** and are **idempotent** (safe to run repeatedly):

1. **Database migrations** – `alembic upgrade head` runs. Only pending migrations are applied; if the database is already up to date, nothing runs.
2. **Default admin user** – If env vars `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_EMAIL`, and `DEFAULT_ADMIN_PASSWORD` are set, a user is created **only if** that username/email does not already exist. If the user exists or env vars are not set, this step is skipped.

No manual migration or user creation is required for first run. Set the default admin in `docker-compose.yml` (or env) and start the stack:

```bash
docker compose up -d
```

Default admin (from root `docker-compose.yml`): `admin` / `admin@example.com` / `admin` (change in production).

### Default User Environment Variables

| Variable | Description |
|----------|-------------|
| `DEFAULT_ADMIN_USERNAME` | Username for the default admin (create only if not set: skip) |
| `DEFAULT_ADMIN_EMAIL` | Email for the default admin |
| `DEFAULT_ADMIN_PASSWORD` | Password for the default admin |
| `DEFAULT_ADMIN_FIRST_NAME` | Optional; default `Admin` |
| `DEFAULT_ADMIN_LAST_NAME` | Optional; default `User` |

If any of the three required vars are missing, default user creation is skipped.

---

## Manual Operations (Optional)

Use these only when you need to create new migrations, roll back, or manage users beyond the default admin.

### Migrations

```bash
# Check current migration status
docker compose exec platform_web uv run alembic current

# View migration history
docker compose exec platform_web uv run alembic history

# Create a new migration after model changes
docker compose exec platform_web uv run alembic revision --autogenerate -m "description"

# Rollback one migration
docker compose exec platform_web uv run alembic downgrade -1
```

### User Management CLI

```bash
# Create a user (interactive or with flags)
docker compose exec -it platform_web uv run platform-cli create-user
docker compose exec platform_web uv run platform-cli create-user --username bob --email bob@example.com --password secret --admin

# List users
docker compose exec platform_web uv run platform-cli list-users

# Initialize database tables (only if not using migrations)
docker compose exec platform_web uv run platform-cli init-db
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/auth/login` | User authentication |

## Configuration

Edit `config.toml` to configure the application.

Environment variables can override config file settings:
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`
- `SECRET_KEY`
- `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD` (see Automated Startup)

## Development

### Backend

The Flask backend runs on port 5000 internally and supports hot reloading in development mode.

```bash
# Run locally
cd platform
uv sync
DATABASE_HOST=localhost uv run python -m backend.app
```

### Frontend

The React frontend uses Vite for development with hot module replacement (HMR).

```bash
# Run locally
cd platform/ui
npm install
npm run dev
```

### Adding shadcn Components

```bash
cd platform/ui
npx shadcn@latest add <component-name>
```

## Production Deployment

### Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| `FLASK_ENV` | `development` | `production` |
| Backend | Flask dev server | Gunicorn (4 workers) |
| Frontend | Vite dev server (HMR) | Pre-built static files |
| Nginx config | `nginx.conf` (proxies to Vite) | `nginx.prod.conf` (serves static) |
| Volumes | Mounted for hot reload | None (built into image) |

### Production Docker Compose

Create `docker-compose.prod.yml` in the repository root:

```yaml
version: '3.8'

services:
  platform_db:
    image: postgres:16-alpine
    container_name: platform_db
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - platform_db_data:/var/lib/postgresql/data
    restart: always

  platform_web:
    build:
      context: ./platform
      dockerfile: Dockerfile
    container_name: platform_web
    environment:
      FLASK_ENV: production
      DATABASE_HOST: platform_db
      DATABASE_PORT: 5432
      DATABASE_NAME: ${DB_NAME}
      DATABASE_USER: ${DB_USER}
      DATABASE_PASSWORD: ${DB_PASSWORD}
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "80:80"
    depends_on:
      platform_db:
        condition: service_healthy
    restart: always

volumes:
  platform_db_data:
```

### Environment File

Create `.env.prod` (do not commit to version control):

```bash
DB_USER=platform
DB_PASSWORD=strong-random-password-here
DB_NAME=platform
SECRET_KEY=another-strong-random-secret
```

### Deploy

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

### Additional Production Considerations

- **SSL/TLS**: Work with hospitals to get DNS set up and to get TLS certs
- **Database**: Use a managed DB (NOTE: most hospitals provide managed MSSQL)
- **Secrets**: Use Docker secrets or a vault instead of env files
- **Logging**: Configure centralized logging (ELK, CloudWatch, etc.)
- **Backups**: Set up automated database backup strategy
- **Monitoring**: Add health check monitoring and alerting
