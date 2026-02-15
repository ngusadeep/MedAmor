"""RAG: index docs (knowledge base) into ChromaDB, retrieve context for audit engine.

Ingests only when new/changed documents exist under medical_kb_path; otherwise skips re-index.
Uses ChromaDB for vector store; embedding via FastEmbed (bge-small) or OpenAI text-embedding-3-small.
"""

import json
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

COLLECTION_NAME = "medaudit_kb"
CHUNK_SIZE = 2048
CHUNK_OVERLAP = 256
DOCUMENT_TYPES = ("Documentation", "SOPs", "User_Manuals", "FAQs", "Clinical_Guidelines")


def _get_embeddings() -> Embeddings:
    """Return embedding model: OpenAI text-embedding-3-small if configured, else FastEmbed bge-small."""
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")


def _get_chroma_persist_dir() -> Path:
    return Path(settings.chroma_persist_dir).resolve()


MANIFEST_FILENAME = "kb_index_manifest.json"


def _manifest_path() -> Path:
    return _get_chroma_persist_dir() / MANIFEST_FILENAME


def _current_doc_signatures(kb_path: Path) -> list[tuple[str, float]]:
    """Return [(rel_path, mtime), ...] for all .md under kb_path."""
    out: list[tuple[str, float]] = []
    if not kb_path.exists():
        return out
    for path in kb_path.rglob("*.md"):
        try:
            rel = path.relative_to(kb_path)
            out.append((str(rel).replace("\\", "/"), path.stat().st_mtime))
        except Exception:
            continue
    return sorted(out)


def _load_manifest() -> list[tuple[str, float]] | None:
    """Load stored manifest; return list of (path, mtime) or None if missing/invalid."""
    p = _manifest_path()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return [tuple(x) for x in data.get("sources", [])]
    except Exception:
        return None


def _save_manifest(sources: list[tuple[str, float]]) -> None:
    """Persist manifest after successful index."""
    p = _manifest_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"sources": [list(s) for s in sources]}, indent=2),
        encoding="utf-8",
    )


def needs_reindex() -> bool:
    """True if KB has new or changed docs compared to last index (or no index yet)."""
    kb_path = settings.medical_kb_path_resolved
    current = _current_doc_signatures(kb_path)
    if not current:
        return False
    stored = _load_manifest()
    if stored is None:
        return True
    return set(current) != set(stored)


def ensure_indexed() -> dict:
    """
    If docs have new/changed files compared to last index, run index_kb(). Else no-op.
    Call on backend startup so ChromaDB is populated from docs when needed.
    """
    if not needs_reindex():
        return {"indexed": 0, "chunks": 0, "skipped": True, "message": "No new or changed documents"}
    result = index_kb()
    if result.get("error"):
        return result
    kb_path = settings.medical_kb_path_resolved
    result["skipped"] = False
    _save_manifest(_current_doc_signatures(kb_path))
    return result


def _get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(_get_chroma_persist_dir()))


def _get_chroma_store() -> Chroma:
    """Chroma vector store with persistent storage."""
    client = _get_chroma_client()
    return Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=_get_embeddings(),
    )


def _document_type_from_path(rel_path: Path) -> str | None:
    """Derive document_type from first path component (e.g. SOPs, Documentation)."""
    parts = rel_path.parts
    if parts and parts[0] in DOCUMENT_TYPES:
        return parts[0]
    return None


def load_kb_documents(kb_path: Path) -> list[tuple[str, dict]]:
    """Load all .md files under kb_path; return (content, metadata) per file."""
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
    Chunk Medical_KB markdown, embed, and persist to ChromaDB.
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
    documents: list[Document] = []
    for content, meta in raw:
        chunks = splitter.split_text(content)
        for c in chunks:
            documents.append(
                Document(
                    page_content=c,
                    metadata={
                        "source": meta.get("source", ""),
                        "document_name": meta.get("document_name", ""),
                        "document_type": meta.get("document_type", ""),
                    },
                )
            )

    if not documents:
        return {"indexed": len(raw), "chunks": 0}

    persist_dir = _get_chroma_persist_dir()
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = _get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    vectorstore = _get_chroma_store()
    vectorstore.add_documents(documents)

    return {"indexed": len(raw), "chunks": len(documents)}


def retrieve(query: str, k: int = 5) -> list[dict]:
    """
    Retrieve top-k relevant KB chunks for the query.
    Returns list of {"text", "source", "document_name", "document_type", "score"}.
    """
    vectorstore = _get_chroma_store()
    try:
        results = vectorstore.similarity_search_with_score(query, k=k)
    except Exception:
        return []

    return [
        {
            "text": doc.page_content,
            "source": doc.metadata.get("source", ""),
            "document_name": doc.metadata.get("document_name", ""),
            "document_type": doc.metadata.get("document_type", ""),
            "score": float(score) if score is not None else 0.0,
        }
        for doc, score in results
    ]


def retrieve_with_patient_context(
    query: str,
    k: int = 5,
    patient_id: str | None = None,
    export_type: str = "full",
) -> dict:
    """
    Retrieve KB chunks and optionally patient EHR excerpt.
    Returns {"query", "kb_chunks": [...], "patient_ehr_excerpt": str | None}.
    """
    kb_chunks = retrieve(query, k=k)
    patient_ehr_excerpt: str | None = None
    if patient_id:
        from app.services.ehr_mock import get_patient_bundle

        bundle = get_patient_bundle(patient_id, export_type)
        if bundle and bundle.ehr_text:
            patient_ehr_excerpt = bundle.ehr_text[:20000]
    return {
        "query": query,
        "kb_chunks": kb_chunks,
        "patient_ehr_excerpt": patient_ehr_excerpt,
    }
