# EHR Data Service - FastAPI, serves patients/ and patients/{id} for backend
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir "fastapi>=0.104" "uvicorn[standard]>=0.24"
COPY server.py .
ENV EHR_DATA_PATH=/data
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
