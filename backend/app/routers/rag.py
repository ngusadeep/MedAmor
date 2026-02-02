"""RAG API: index Medical_KB, retrieve context for audit."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user_required
from app.models.user import User
from app.services import rag

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/index")
def index_kb(_user: User = Depends(get_current_user_required)):
    """Chunk and index Medical_KB markdown into Qdrant. Idempotent (recreates collection)."""
    try:
        result = rag.index_kb()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/retrieve")
def retrieve(
    query: str,
    k: int = 5,
    _user: User = Depends(get_current_user_required),
):
    """Retrieve top-k KB chunks relevant to the query (for audit context)."""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="query is required")
    try:
        chunks = rag.retrieve(query.strip(), k=min(k, 20))
        return {"query": query, "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
