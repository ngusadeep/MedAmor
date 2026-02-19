# Single image for MedAudit backend, Celery worker, Celery beat, and EHR service.
# Build from demo/: docker build -f Dockerfile -t medaudit-app .
# All four Python services use this image with different commands.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

ENV UV_NO_DEV=1

# Backend deps
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Backend app
COPY backend/main.py ./
COPY backend/app/ ./app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# EHR service (same image, run as uvicorn ehr.server:app)
RUN mkdir -p ehr
COPY ehr/server.py ehr/__init__.py ehr/

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
