# MedAudit Backend

FastAPI backend for the MedAudit medical audit system.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Environment setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the server:**
   ```bash
   python main.py
   ```

   Or with uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

## API Documentation

Once running, visit:
- API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Development

- Python 3.12+
- FastAPI framework
- Uvicorn ASGI server
- Pydantic for data validation

## Project Structure

```
backend/
├── main.py          # FastAPI application
├── pyproject.toml   # Project configuration
├── .env.example     # Environment variables template
└── README.md        # This file
```