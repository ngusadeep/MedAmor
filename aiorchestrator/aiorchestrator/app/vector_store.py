"""ChromaDB vector store with Google Embeddings for clinical guidelines."""

from __future__ import annotations

import os
from pathlib import Path

from chromadb.config import Settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma


EMBEDDING_MODEL = "models/gemini-embedding-001"
CHROMA_COLLECTION = "medaudit_guidelines"
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_data")


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Create Google Generative AI embeddings client."""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
    )


def get_vector_store(
    persist_directory: str | None = None,
    collection_name: str = CHROMA_COLLECTION,
) -> Chroma:
    """Get or create ChromaDB vector store with Google Embeddings."""
    persist = persist_directory or CHROMA_PERSIST_DIR
    embeddings = get_embeddings()
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist,
        client_settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )


def _split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def ingest_guidelines(
    guidelines_dir: str | Path,
    vector_store: Chroma | None = None,
) -> int:
    """Load markdown guideline files into the vector store. Returns count of chunks added."""
    path = Path(guidelines_dir)
    if not path.exists():
        return 0

    all_chunks: list[tuple[str, dict]] = []
    for md_file in path.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        for chunk in _split_text(content):
            all_chunks.append((chunk, {"source": str(md_file.relative_to(path))}))

    if not all_chunks:
        return 0

    vs = vector_store or get_vector_store()
    vs.add_texts([c[0] for c in all_chunks], metadatas=[c[1] for c in all_chunks])
    return len(all_chunks)
