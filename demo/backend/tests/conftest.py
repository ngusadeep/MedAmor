"""Pytest fixtures and config for MedAudit backend tests."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Temporary directory; cleaned up after test."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def kb_path_with_one_file(temp_dir):
    """A temp KB path containing one .md file (for RAG tests)."""
    kb = temp_dir / "kb"
    kb.mkdir()
    (kb / "Doc.md").write_text("# Hello\n\nSome content.", encoding="utf-8")
    return kb


@pytest.fixture
def chroma_dir(temp_dir):
    """A temp directory for ChromaDB persist (avoid touching real chroma_data)."""
    return temp_dir / "chroma"
