"""RAG API: index Medical_KB, retrieve context for audit."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user_required
from app.models.user import User
from app.services import rag

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/index")
def index_kb(_user: User = Depends(get_current_user_required)):
    """Chunk and index Medical_KB markdown into ChromaDB. Idempotent (recreates collection)."""
    try:
        result = rag.index_kb()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/retrieve")
def retrieve(
    query: str,
    k: int = 5,
    patient_id: str | None = None,
    export_type: str = "full",
    _user: User = Depends(get_current_user_required),
):
    """Retrieve top-k KB chunks for the query. Optionally include patient EHR context (Phase 2.4)."""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="query is required")
    try:
        k = min(k, 20)
        if patient_id:
            result = rag.retrieve_with_patient_context(
                query.strip(), k=k, patient_id=patient_id, export_type=export_type
            )
            return result
        chunks = rag.retrieve(query.strip(), k=k)
        return {"query": query.strip(), "chunks": chunks, "kb_chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
