# Platform

A web application platform built with Flask, React, TypeScript, and PostgreSQL.

## Project Structure

```
platform/
├── backend/                 # Flask backend
│   ├── __init__.py
│   ├── app.py              # Flask application factory
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




## Database Migrations

```bash
# Run migrations
sudo docker-compose exec platform_web uv run alembic upgrade head

# Create a new migration after model changes
docker compose exec platform_web uv run alembic revision --autogenerate -m "description"
```






## Database Migrations

This project uses Alembic for database migrations.

**NOTE**: Migrations run automatically during build, so
the migrations will rarely need to be run


### Running Migrations

**Recommended via docker:**

```bash
# Run all pending migrations
docker compose exec platform_web uv run alembic upgrade head

# Check current migration status
docker compose exec platform_web uv run alembic current

# View migration history
docker compose exec platform_web uv run alembic history
```


### Creating New Migrations

**Auto-generate from model changes:**

```bash
docker compose exec platform_web uv run alembic revision --autogenerate -m "description of changes"
```


### Rollback Migrations

Look up alembic notes for more rollback options

```bash
# Rollback one migration
docker compose exec platform_web uv run alembic downgrade -1
```



## Configuration

Edit `platform/config.toml` to configure the application:





## User Management CLI

Create and manage users via the command line.

### Create a User

**Interactive mode:**

```bash
docker compose exec -it platform_web uv run platform-cli create-user
```

**Non-interactive mode:**

```bash
docker compose exec platform_web uv run platform-cli create-user \
  --username admin \
  --email admin@example.com \
  --password yourpassword \
  --admin
```


### List Users

```bash
docker compose exec platform_web uv run platform-cli list-users
```

### Initialize Database Tables

```bash
docker compose exec platform_web uv run platform-cli init-db
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/users` | List all users |
| GET | `/api/users/:id` | Get user by ID |
| POST | `/api/users` | Create new user |
| PUT | `/api/users/:id` | Update user |
| DELETE | `/api/users/:id` | Delete user |

## Configuration

Edit `config.toml` to configure the application:

```toml
[database]
host = "platform_db"
port = 5432
name = "platform"
user = "platform"
password = "platform_dev_password"

[server]
host = "0.0.0.0"
port = 5000
debug = true
secret_key = "change-this-in-production"

[security]
password_hash_rounds = 12
```

Environment variables can override config file settings:
- `DATABASE_HOST`
- `DATABASE_PORT`
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`
- `SECRET_KEY`

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
    # No volume mounts - uses built code

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
