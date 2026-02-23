"""EHR data service: FastAPI app that serves patient data from PostgreSQL.

Response format matches backend schemas EHRPatientSummary, EHRPatientDetail,
and EHRPatientBundle so the backend can proxy requests from the frontend.
"""

import subprocess
import sys
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from ehr.app.core.config import settings
from ehr.app.database.connection import Base, SessionLocal, engine
from ehr.app.routes.health import router as health_router
from ehr.app.routes.patients import router as patients_router

_migration_lock = threading.Lock()
_migration_done = threading.Event()


def _schema_needs_update() -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'patients' AND column_name = 'birth_date'"
            )
        )
        return result.fetchone() is None


def _recreate_table() -> None:
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS patients CASCADE"))
        conn.commit()
    Base.metadata.create_all(bind=engine)


def _run_migration_subprocess() -> None:
    with _migration_lock:
        result = subprocess.run(
            [sys.executable, "ehr/migrate_from_fhir.py"],
            cwd="/app",
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("FHIR migration completed.")
            print(result.stdout[-3000:])
        else:
            print(f"FHIR migration failed:\n{result.stderr[-3000:]}")
        _migration_done.set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    needs_migration = False

    if _schema_needs_update():
        print("Schema out of date — recreating patients table...")
        _recreate_table()
        needs_migration = True
    else:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            from ehr.app.database.patient_service import get_all_patients
            if not get_all_patients(db):
                needs_migration = True

    if needs_migration:
        print("Starting FHIR migration in background...")
        t = threading.Thread(target=_run_migration_subprocess, daemon=True)
        t.start()
    else:
        _migration_done.set()

    yield  # server is up and accepting requests immediately


app = FastAPI(title="EHR Data Service", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(patients_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )
