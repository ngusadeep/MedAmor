# MedAudit Backend - Python 3.12
FROM python:3.12-slim-bookworm

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY main.py ./
COPY app/ ./app/

# Install application and dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "uvicorn[standard]>=0.24.0" \
    && pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
