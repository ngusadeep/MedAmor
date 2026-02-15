"""
MedAudit Backend API
FastAPI application for medical audit system.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers import audit_reports, auth, ehr, jobs, patients, rag


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables; ensure RAG KB is indexed (only if new/changed docs in docs/)."""
    init_db()
    try:
        from app.services import rag
        rag.ensure_indexed()
    except Exception:
        pass
    yield


app = FastAPI(
    title="MedAudit Backend API",
    description="Medical audit system backend — jobs, audit reports, mock EHR",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(audit_reports.router, prefix="/api")
app.include_router(ehr.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(rag.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "MedAudit Backend API", "status": "running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug and settings.environment == "development",
    )
