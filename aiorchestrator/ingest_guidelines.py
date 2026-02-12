#!/usr/bin/env python3
"""Ingest Medical Knowledge Base into ChromaDB for RAG retrieval.

Usage:
    python ingest_guidelines.py [--kb-path PATH] [--force]

This script loads all markdown files from the Medical_KB directory,
chunks them, and stores them in ChromaDB with Google Embeddings.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from aiorchestrator.app.vector_store import get_vector_store, ingest_guidelines


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Ingest medical guidelines into ChromaDB")
    parser.add_argument(
        "--kb-path",
        type=str,
        default=os.environ.get("MEDICAL_KB_PATH", "../docs/Medical_KB"),
        help="Path to Medical Knowledge Base directory (default: ../docs/Medical_KB)",
    )
    parser.add_argument(
        "--chroma-dir",
        type=str,
        default=os.environ.get("CHROMA_PERSIST_DIR", "./chroma_data"),
        help="ChromaDB persistence directory (default: ./chroma_data)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reset existing vector store before ingestion",
    )
    args = parser.parse_args()

    # Validate Google API Key
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY not found in environment")
        print("Please set it in .env file or export it:")
        print("  export GOOGLE_API_KEY=your_key_here")
        sys.exit(1)

    # Resolve KB path
    kb_path = Path(args.kb_path)
    if not kb_path.exists():
        print(f"ERROR: Medical KB path not found: {kb_path}")
        print(f"Current directory: {Path.cwd()}")
        sys.exit(1)

    print(f"Medical Knowledge Base: {kb_path.resolve()}")
    print(f"ChromaDB Directory: {args.chroma_dir}")
    print()

    # Get or create vector store
    if args.force:
        print("Resetting existing vector store...")
        try:
            vs = get_vector_store(persist_directory=args.chroma_dir)
            vs.delete_collection()
            print("Vector store reset complete")
        except Exception as e:
            print(f"Note: Could not reset vector store (may not exist yet): {e}")

    # Ingest guidelines
    print("Ingesting medical guidelines...")
    print("This may take a few minutes as documents are embedded...")
    try:
        vs = get_vector_store(persist_directory=args.chroma_dir)
        chunk_count = ingest_guidelines(kb_path, vs)
        print(f"✓ Successfully ingested {chunk_count} text chunks")
        print()
        print("Vector store ready for RAG retrieval!")
        print(f"Persisted to: {Path(args.chroma_dir).resolve()}")

    except Exception as e:
        print(f"ERROR during ingestion: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
