# MedArmor Backend - Python 3.12, deps via uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Omit dev dependencies
ENV UV_NO_DEV=1

# Copy dependency files first (better layer cache)
COPY pyproject.toml uv.lock ./

# Install dependencies only (no project yet)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy application code
COPY main.py ./
COPY app/ ./app/

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
