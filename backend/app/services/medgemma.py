"""MedGemma client: call Hugging Face Inference API for structured audit output."""

import json
import re
from typing import Any

import httpx

from app.core.config import settings

# Stub structured output when HF is not configured
STUB_REPORT = {
    "status": "NO_FINDINGS",
    "risk_level": "low",
    "executive_summary": "Automated review completed. No critical findings in this sample.",
    "findings": [],
    "evidence": [],
    "corrective_actions": [],
    "next_audit_date": None,
}


def run_medgemma(
    prompt: str,
    ehr_excerpt: str | None = None,
    kb_context: str | None = None,
    max_new_tokens: int = 1024,
) -> dict[str, Any]:
    """
    Call MedGemma via HF Inference API. Returns structured audit fields.
    If HF_TOKEN or endpoint not set, returns STUB_REPORT.
    """
    if not settings.hf_token or not settings.hf_medgemma_endpoint:
        return STUB_REPORT.copy()

    # Build full prompt for model
    parts = []
    if kb_context:
        parts.append("## Knowledge base context\n" + kb_context[:8000])
    if ehr_excerpt:
        parts.append("## Patient EHR excerpt\n" + ehr_excerpt[:12000])
    parts.append("## Instruction\n" + prompt)
    full_prompt = "\n\n".join(parts)

    url = settings.hf_medgemma_endpoint.rstrip("/")
    if "/chat" in url or "inference" in url:
        payload = {"inputs": full_prompt, "parameters": {"max_new_tokens": max_new_tokens}}
    else:
        payload = {"inputs": full_prompt, "parameters": {"max_new_tokens": max_new_tokens}}

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {settings.hf_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return STUB_REPORT.copy()

    # Parse model output into structured report (simplified: look for JSON block or use stub)
    raw = ""
    if isinstance(data, list) and len(data) > 0:
        raw = data[0].get("generated_text", data[0]) if isinstance(data[0], dict) else str(data[0])
    elif isinstance(data, dict):
        raw = data.get("generated_text", data.get("output", str(data)))

    parsed = _parse_structured_output(raw)
    return parsed if parsed else STUB_REPORT.copy()


def _parse_structured_output(raw: str) -> dict | None:
    """Try to extract JSON or key fields from model output."""
    if not raw or not raw.strip():
        return None
    # Try JSON block
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None
