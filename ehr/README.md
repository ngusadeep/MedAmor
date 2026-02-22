# EHR Data Service

FastAPI service that provides patient EHR data from PostgreSQL database.

## Architecture

- **Database**: PostgreSQL with SQLAlchemy ORM
- **API**: FastAPI with Pydantic schemas
- **Structure**:
  - `app/core/`: Configuration
  - `app/schemas/`: Pydantic models
  - `app/database/`: Database models and services
  - `app/routes/`: API endpoints

## API Endpoints

- `GET /health` - Health check
- `GET /patients` - List all patients
- `GET /patients/{patient_id}` - Get patient EHR bundle

## Data Migration

Patient data is automatically migrated from file system to database on first startup.

## Development

```bash
# Install dependencies
pip install -e .

# Run migration (populate database from files)
python migrate_patients.py

# Run server
python server.py
```
