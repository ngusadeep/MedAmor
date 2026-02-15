"""Tests for RAG: needs_reindex, ensure_indexed, manifest."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.rag import (
    MANIFEST_FILENAME,
    _current_doc_signatures,
    _load_manifest,
    _manifest_path,
    _save_manifest,
    ensure_indexed,
    needs_reindex,
)


def test_current_doc_signatures_empty(tmp_path):
    """Empty or missing dir returns []."""
    assert _current_doc_signatures(tmp_path) == []
    (tmp_path / "empty").mkdir()
    assert _current_doc_signatures(tmp_path / "empty") == []


def test_current_doc_signatures_collects_md(tmp_path):
    """Collects .md files with (rel_path, mtime)."""
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "1.md").write_text("x")
    (tmp_path / "b.md").write_text("y")
    out = _current_doc_signatures(tmp_path)
    assert len(out) == 2
    paths = {p for p, _ in out}
    assert "a/1.md" in paths or "a\\1.md" in paths
    assert "b.md" in paths


def test_manifest_save_load(temp_dir):
    """Save and load manifest round-trip."""
    with patch("app.services.rag._get_chroma_persist_dir", return_value=temp_dir):
        _save_manifest([("a.md", 123.0), ("b/c.md", 456.0)])
        loaded = _load_manifest()
        assert loaded is not None
        assert set(loaded) == {("a.md", 123.0), ("b/c.md", 456.0)}


def test_manifest_path():
    """Manifest path is chroma_persist_dir / kb_index_manifest.json."""
    with patch("app.services.rag._get_chroma_persist_dir", return_value=Path("/tmp/chroma")):
        p = _manifest_path()
        assert p.name == MANIFEST_FILENAME
        assert "chroma" in str(p)


def test_needs_reindex_no_kb(temp_dir):
    """When KB path has no .md files, needs_reindex is False (nothing to index)."""
    with patch("app.services.rag.settings") as s:
        s.medical_kb_path_resolved = temp_dir
        assert needs_reindex() is False


def test_needs_reindex_no_manifest(kb_path_with_one_file):
    """When manifest is missing, needs_reindex is True (KB has files)."""
    with patch("app.services.rag.settings") as s:
        s.medical_kb_path_resolved = kb_path_with_one_file
    with patch("app.services.rag._load_manifest", return_value=None):
        assert needs_reindex() is True


def test_needs_reindex_unchanged_matches_manifest(kb_path_with_one_file):
    """When current signatures match stored manifest, needs_reindex is False."""
    current = _current_doc_signatures(kb_path_with_one_file)
    assert len(current) == 1
    with patch("app.services.rag.settings") as s:
        s.medical_kb_path_resolved = kb_path_with_one_file
        with patch("app.services.rag._load_manifest", return_value=list(current)):
            assert needs_reindex() is False


def test_needs_reindex_new_file(kb_path_with_one_file, temp_dir):
    """When there is an extra file not in manifest, needs_reindex is True."""
    current = _current_doc_signatures(kb_path_with_one_file)
    (kb_path_with_one_file / "new.md").write_text("new")
    current_after = _current_doc_signatures(kb_path_with_one_file)
    assert len(current_after) == 2
    with patch("app.services.rag.settings") as s:
        s.medical_kb_path_resolved = kb_path_with_one_file
    with patch("app.services.rag._load_manifest", return_value=current):
        assert needs_reindex() is True


def test_ensure_indexed_skips_when_no_reindex(temp_dir):
    """ensure_indexed returns skipped when needs_reindex is False."""
    with patch("app.services.rag.needs_reindex", return_value=False):
        out = ensure_indexed()
        assert out.get("skipped") is True
        assert "No new or changed" in out.get("message", "")
