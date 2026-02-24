"""
MedAudit Backend API
FastAPI application for medical audit system.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers import audit_reports, auth, ehr, jobs, patients, rag, transcribe


def _load_medasr_warmup() -> None:
    from app.services.transcription import _load_local_medasr
    _load_local_medasr()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables, index RAG KB, pre-warm local ASR model if configured."""
    import asyncio

    init_db()
    try:
        from app.services import rag

        rag.ensure_indexed()
    except Exception:
        pass

    # Pre-warm local MedASR: await the load so the model is fully in memory before
    # the server begins accepting requests.  The HF cache volume means the download
    # only happens once; subsequent starts just load from disk (~5-10 s on CPU).
    if settings.asr_provider == "medasr_local":
        import logging
        _log = logging.getLogger(__name__)
        try:
            _log.info("Pre-warming local MedASR model…")
            await asyncio.get_event_loop().run_in_executor(None, _load_medasr_warmup)
            _log.info("MedASR local model ready.")
        except Exception as exc:
            _log.warning("MedASR local warmup failed (first transcription will be slow): %s", exc)

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
app.include_router(transcribe.router, prefix="/api")


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
        reload=False,  # Disable reload in container environment
    )
