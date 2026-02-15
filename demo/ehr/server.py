"""EHR data service: FastAPI app that serves patient data from PostgreSQL database.

Response format matches backend schemas EHRPatientSummary and EHRPatientBundle
so the backend can proxy requests from the frontend to this service.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ehr.app.core.config import settings
from ehr.app.database.connection import create_tables
from ehr.app.routes.health import router as health_router
from ehr.app.routes.patients import router as patients_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup: Create database tables
    create_tables()

    # Run migration to populate patients from files (if database is empty)
    from sqlalchemy.orm import Session
    from ehr.app.database.connection import SessionLocal
    from ehr.app.database.patient_service import get_all_patients

    with SessionLocal() as db:
        existing_patients = get_all_patients(db)
        if not existing_patients:
            print("Database is empty, running patient migration...")
            # Import and run migration
            import subprocess
            import sys
            try:
                result = subprocess.run([sys.executable, "ehr/migrate_patients.py"],
                                      cwd="/app",
                                      capture_output=True,
                                      text=True)
                if result.returncode == 0:
                    print("Patient migration completed successfully")
                    print(result.stdout)
                else:
                    print(f"Migration failed: {result.stderr}")
            except Exception as e:
                print(f"Migration error: {e}")

    yield
    # Shutdown: Clean up resources if needed


app = FastAPI(
    title="EHR Data Service",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(patients_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
