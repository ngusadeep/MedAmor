# EHR Server

## Background

There are two modes for running the EHR:

1. Running a HAPI FHIR server
2. Running a lightweight EHR Data Service

The HAPI server is a real FHIR server with a full, unsimulated FHIR API, while the lightweight EHR server can return patient records but does not support other APIs.

For AI agent testing, the lightweight service is preferred. However, for testing platform features that identify patients with modified records, an actual FHIR server such as the HAPI server is required.


## Option 1: HAPI FHIR Server

```
sudo docker compose --env-file ../.env --profile hapi up
```

Note that it can take several minutes without any output before the server
becomes available.

To test the server is running, run the following:

```
curl -X GET "http://localhost:8001/fhir/metadata"
```

Additional management commands are below.


### Loading Data

Data is already prepared for loading. To generate your own or use a different approach, see [data_notes.md](data_notes.md).


### Uploading Data

```
./upload_fhir.sh /fhir/
```

### Other Management Notes

#### See some data

Run this curl to find a patient to get data for (you can remove the
`| jq ...` to see the patient object):

```
curl -s "http://localhost:8001/fhir/Patient?_count=1&_pretty=true" | jq '.entry[0].resource.id'
```

Take that ID (e.g. `26171`) and use it to retrieve the full patient chart:

```
curl "http://localhost:8001/fhir/Patient/26171/\$everything?_pretty=true"
```

You may also use the interactive browser in the
`orchestrator/interactive_fhir_browser` (see the README there).

#### Taking the server down

```
sudo docker compose down
```

#### Resetting the DB

First take the server down, then:

```
sudo docker volume rm hapi_db_data
```



## Lightweight EHR Data Service

FastAPI service that serves patient EHR data from a PostgreSQL database.

```
sudo docker compose --env-file ../.env --profile ehr_data up
```

### Architecture

- **Database**: PostgreSQL with SQLAlchemy ORM
- **API**: FastAPI with Pydantic schemas
- **Structure**:
  - `app/core/`: Configuration
  - `app/schemas/`: Pydantic models
  - `app/database/`: Database models and services
  - `app/routes/`: API endpoints

### API Endpoints

- `GET /health` - Health check
- `GET /patients` - List all patients
- `GET /patients/{patient_id}` - Get patient EHR bundle

### Data Migration

Patient data is automatically migrated from the file system to the database on first startup.

### Development

```bash
# Install dependencies
pip install -e .

# Run migration (populate database from files)
python migrate_patients.py

# Run server
python server.py
```
