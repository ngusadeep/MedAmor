#!/usr/bin/env python3
"""Test ChromaDB and vector store functionality."""

import os
from pathlib import Path

print("Testing ChromaDB Vector Store...")
print("-" * 60)

# Check for Google API key
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("⚠ GOOGLE_API_KEY not set in environment")
    print("  Set it in .env file or export it:")
    print("  export GOOGLE_API_KEY=your_key_here")
    print("\nSkipping vector store tests (need API key for embeddings)")
    exit(0)

print(f"✓ Google API Key found: {api_key[:8]}...")

# Test vector store initialization
print("\n1. Testing vector store initialization:")
try:
    from aiorchestrator.app.vector_store import get_vector_store

    vs = get_vector_store()
    print(f"✓ Vector store initialized")
    print(f"  Collection: medaudit_guidelines")
    print(f"  Persist dir: ./chroma_data")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

# Test adding dummy documents
print("\n2. Testing document ingestion:")
try:
    test_docs = [
        "Hypertension treatment requires blood pressure monitoring.",
        "Diabetes management includes HbA1c testing every 3 months.",
        "COVID-19 treatment protocol involves isolation and monitoring.",
    ]
    test_metadata = [
        {"source": "test_hypertension.md"},
        {"source": "test_diabetes.md"},
        {"source": "test_covid.md"},
    ]

    vs.add_texts(test_docs, metadatas=test_metadata)
    print(f"✓ Added {len(test_docs)} test documents")
except Exception as e:
    print(f"✗ Error adding documents: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

# Test similarity search
print("\n3. Testing similarity search:")
try:
    results = vs.similarity_search("blood pressure treatment", k=2)
    print(f"✓ Search returned {len(results)} results")
    for i, doc in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Content: {doc.page_content[:80]}...")
        print(f"    Source: {doc.metadata.get('source', 'N/A')}")
except Exception as e:
    print(f"✗ Error during search: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

print("\n" + "-" * 60)
print("✓ Vector store tests passed!")
print("\nNow you can run: python ingest_guidelines.py")
print("to load the full Medical KB")
