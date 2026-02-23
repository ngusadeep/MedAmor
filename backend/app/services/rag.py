"""RAG: index docs (knowledge base) into ChromaDB, retrieve context for audit engine.

Ingests only when new/changed documents exist under medical_kb_path; otherwise skips re-index.

Embedding providers
-------------------
fastembed   – sentence-transformers/all-MiniLM-L6-v2 via FastEmbed (default, no API key)
openai      – OpenAI text-embedding-3-small (requires OPENAI_API_KEY)
medsiglip   – google/medsiglip-448 text encoder via transformers (requires torch, HF_TOKEN)
              NOTE: 64-token context limit — chunk size is reduced to 256 chars automatically.
              Better suited for future image retrieval; text-only RAG works but truncates long chunks.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "medaudit_kb"
# Default chunk sizes — MedSigLIP overrides to 256 due to 64-token limit
CHUNK_SIZE = 2048
CHUNK_OVERLAP = 256
# MedSigLIP text encoder hard limit is 64 tokens ≈ 200-250 English chars.
# We use 256 chars with 32 overlap to stay safely under the limit.
MEDSIGLIP_CHUNK_SIZE = 256
MEDSIGLIP_CHUNK_OVERLAP = 32

DOCUMENT_TYPES = (
    "Documentation",
    "SOPs",
    "User_Manuals",
    "FAQs",
    "Clinical_Guidelines",
)


# ---------------------------------------------------------------------------
# MedSigLIP text embeddings (google/medsiglip-448)
# ---------------------------------------------------------------------------

class MedSigLIPEmbeddings(Embeddings):
    """LangChain Embeddings adapter for google/medsiglip-448 text encoder.

    Uses SiglipTextModel directly (no image input required) so it can be used
    as a drop-in embedding provider for text-only RAG.

    Important limitation: the SigLIP text encoder has a 64-token context window.
    Texts longer than ~250 chars will be truncated.  Use MEDSIGLIP_CHUNK_SIZE
    (256 chars) when indexing to stay within this limit.
    """

    def __init__(
        self,
        model_id: str = "google/medsiglip-448",
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        self.model_id = model_id
        self.device = device
        self.batch_size = batch_size
        self._model: Any = None
        self._tokenizer: Any = None
        self._lock = threading.Lock()

    def _load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            from transformers import AutoTokenizer, SiglipTextModel

            logger.info(
                "Loading MedSigLIP text encoder '%s' on device '%s'…",
                self.model_id,
                self.device,
            )
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self._model = SiglipTextModel.from_pretrained(self.model_id).to(
                self.device
            )
            self._model.eval()
            logger.info("MedSigLIP text encoder loaded.")

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        import torch

        self._load()
        inputs = self._tokenizer(
            texts,
            padding="max_length",
            max_length=64,  # hard limit per MedSigLIP model card
            truncation=True,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model(**inputs)
            # pooler_output: (batch, hidden_dim) — the [CLS] representation
            embeds = outputs.pooler_output
            # L2 normalise so cosine similarity works correctly
            embeds = embeds / embeds.norm(dim=-1, keepdim=True)

        return embeds.cpu().float().tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            results.extend(self._embed_batch(texts[i : i + self.batch_size]))
        return results

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]


# Singleton so the model is loaded once per process
_medsiglip_instance: MedSigLIPEmbeddings | None = None
_medsiglip_lock = threading.Lock()


def _get_medsiglip_embeddings() -> MedSigLIPEmbeddings:
    global _medsiglip_instance
    if _medsiglip_instance is not None:
        return _medsiglip_instance
    with _medsiglip_lock:
        if _medsiglip_instance is None:
            _medsiglip_instance = MedSigLIPEmbeddings(
                model_id=settings.medsiglip_model,
                device=settings.medsiglip_device,
            )
    return _medsiglip_instance


# ---------------------------------------------------------------------------
# Embedding provider selection
# ---------------------------------------------------------------------------

def _get_embeddings() -> Embeddings:
    """Return the configured embedding model.

    Providers:
      fastembed   – sentence-transformers/all-MiniLM-L6-v2 (default)
      openai      – OpenAI text-embedding-3-small
      medsiglip   – google/medsiglip-448 text encoder (64-token limit)
    """
    provider = settings.embedding_provider.lower()

    if provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )

    if provider == "medsiglip":
        return _get_medsiglip_embeddings()

    # Default: FastEmbed with all-MiniLM-L6-v2
    # (BAAI/bge-small-en-v1.5 can fail with missing model_optimized.onnx)
    return FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def _get_chunk_params() -> tuple[int, int]:
    """Return (chunk_size, chunk_overlap) appropriate for the current embedding provider."""
    if settings.embedding_provider.lower() == "medsiglip":
        logger.warning(
            "MedSigLIP embedding selected: reducing chunk size to %d chars "
            "(64-token context limit). Long guideline sections will be split more aggressively.",
            MEDSIGLIP_CHUNK_SIZE,
        )
        return MEDSIGLIP_CHUNK_SIZE, MEDSIGLIP_CHUNK_OVERLAP
    return CHUNK_SIZE, CHUNK_OVERLAP


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
        return {
            "indexed": 0,
            "chunks": 0,
            "skipped": True,
            "message": "No new or changed documents",
        }
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

    chunk_size, chunk_overlap = _get_chunk_params()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
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
            patient_ehr_excerpt = bundle.ehr_text
    return {
        "query": query,
        "kb_chunks": kb_chunks,
        "patient_ehr_excerpt": patient_ehr_excerpt,
    }
