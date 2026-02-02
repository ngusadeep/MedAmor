"""RAG: index Medical_KB markdown into Qdrant, retrieve context for audit engine.

Phase 2: 384–768 token chunks, document_type metadata, retrieval with optional patient context.
"""

from pathlib import Path

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

COLLECTION_NAME = "medaudit_kb"
# ~512 tokens at ~4 chars/token (Phase 2.1: 384–768 token chunks)
CHUNK_SIZE = 2048
CHUNK_OVERLAP = 256
DOCUMENT_TYPES = ("Documentation", "SOPs", "User_Manuals", "FAQs")


def _get_qdrant_client() -> QdrantClient:
    url = settings.qdrant_url
    api_key = settings.qdrant_api_key
    return QdrantClient(url=url, api_key=api_key or None)


def _get_embeddings() -> FastEmbedEmbeddings:
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")


def _document_type_from_path(rel_path: Path) -> str | None:
    """Derive document_type from first path component (e.g. SOPs, Documentation)."""
    parts = rel_path.parts
    if parts and parts[0] in DOCUMENT_TYPES:
        return parts[0]
    return None


def load_kb_documents(kb_path: Path) -> list[tuple[str, dict]]:
    """Load all .md files under kb_path; return (content, metadata) per file.
    Metadata: source, path, document_name, document_type (from folder)."""
    docs: list[tuple[str, dict]] = []
    if not kb_path.exists():
        return docs
    for path in kb_path.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(kb_path)
            document_type = _document_type_from_path(rel)
            metadata = {
                "source": str(rel),
                "path": str(path),
                "document_name": path.name,
                "document_type": document_type or "",
            }
            docs.append((text, metadata))
        except Exception:
            continue
    return docs


def index_kb() -> dict:
    """
    Chunk Medical_KB markdown, embed with FastEmbed, upsert to Qdrant.
    Returns counts and any error message.
    """
    kb_path = settings.medical_kb_path_resolved
    raw = load_kb_documents(kb_path)
    if not raw:
        return {"indexed": 0, "chunks": 0, "error": "No markdown files found"}

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    texts: list[str] = []
    metadatas: list[dict] = []
    for content, meta in raw:
        chunks = splitter.split_text(content)
        for c in chunks:
            texts.append(c)
            metadatas.append(meta.copy())

    if not texts:
        return {"indexed": len(raw), "chunks": 0}

    client = _get_qdrant_client()
    embeddings_model = _get_embeddings()
    dim = len(embeddings_model.embed_query("dummy"))

    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    vectors = embeddings_model.embed_documents(texts)
    points = [
        PointStruct(
            id=i,
            vector=v,
            payload={
                "text": t,
                "source": m.get("source", ""),
                "document_name": m.get("document_name", ""),
                "document_type": m.get("document_type", ""),
            },
        )
        for i, (v, t, m) in enumerate(zip(vectors, texts, metadatas))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    return {"indexed": len(raw), "chunks": len(texts)}


def retrieve(query: str, k: int = 5) -> list[dict]:
    """
    Retrieve top-k relevant KB chunks for the query.
    Returns list of {"text", "source", "document_name", "document_type", "score"}.
    """
    client = _get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        return []

    embeddings_model = _get_embeddings()
    query_vector = embeddings_model.embed_query(query)
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=k,
    )
    return [
        {
            "text": hit.payload.get("text", ""),
            "source": hit.payload.get("source", ""),
            "document_name": hit.payload.get("document_name", ""),
            "document_type": hit.payload.get("document_type", ""),
            "score": float(hit.score) if hit.score is not None else 0.0,
        }
        for hit in results
    ]


def retrieve_with_patient_context(
    query: str,
    k: int = 5,
    patient_id: str | None = None,
    export_type: str = "full",
) -> dict:
    """
    Retrieve KB chunks and optionally patient EHR excerpt (Phase 2.4).
    Returns {"query", "kb_chunks": [...], "patient_ehr_excerpt": str | None}.
    """
    kb_chunks = retrieve(query, k=k)
    patient_ehr_excerpt: str | None = None
    if patient_id:
        from app.services.ehr_mock import get_patient_bundle

        bundle = get_patient_bundle(patient_id, export_type)
        if bundle and bundle.ehr_text:
            # Truncate for context window; audit engine may truncate again
            patient_ehr_excerpt = bundle.ehr_text[:20000]
    return {
        "query": query,
        "kb_chunks": kb_chunks,
        "patient_ehr_excerpt": patient_ehr_excerpt,
    }
