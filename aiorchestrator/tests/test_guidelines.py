"""Tests for GuidelineStore and GuidelineRetriever."""

import tempfile
from pathlib import Path

import pytest

from aiorchestrator.guidelines.store import GuidelineStore, GuidelineChunk
from aiorchestrator.guidelines.retriever import GuidelineRetriever


def test_guideline_store_loads_and_returns_chunks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "diabetes_management").mkdir()
        (Path(tmp) / "diabetes_management" / "protocol.md").write_text(
            "## Purpose\nManage diabetes.\n\n## Key\n- HbA1c",
            encoding="utf-8",
        )
        store = GuidelineStore(guidelines_dir=tmp)
        store.load()
        chunks = store.get_chunks_for_audit_type("diabetes_management")
        assert len(chunks) >= 1
        assert all(isinstance(c, GuidelineChunk) for c in chunks)
        assert all(c.audit_type == "diabetes_management" for c in chunks)


def test_guideline_retriever_returns_relevant_chunks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "medication_safety").mkdir()
        (Path(tmp) / "medication_safety" / "protocol.md").write_text(
            "## Purpose\nMedication safety.\n\n## Key\nReconciliation.",
            encoding="utf-8",
        )
        store = GuidelineStore(guidelines_dir=tmp)
        store.load()
        retriever = GuidelineRetriever(store=store, top_k=5)
        chunks = retriever.retrieve(
            "medication_safety", "patient on warfarin and metformin"
        )
        assert len(chunks) <= 5
        assert all(c.audit_type == "medication_safety" for c in chunks)
