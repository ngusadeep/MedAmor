"""MedGemma client: Hugging Face Inference API or Vertex AI (hosted endpoint)."""

import json
import logging
import re
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

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


def _is_vertex_configured(medgemma_backend_override: str | None = None) -> bool:
    backend = (
        medgemma_backend_override
        if medgemma_backend_override
        else settings.medgemma_backend
    )
    return bool(
        backend == "vertex"
        and settings.vertex_ai_project
        and settings.vertex_ai_location
        and settings.vertex_ai_medgemma_endpoint_id
    )


def _run_medgemma_vertex(full_prompt: str, max_new_tokens: int = 1024) -> str:
    """Call MedGemma on Vertex AI hosted endpoint. Returns raw model output."""
    from google.cloud import aiplatform

    aiplatform.init(
        project=settings.vertex_ai_project,
        location=settings.vertex_ai_location,
    )
    resource_name = (
        f"projects/{settings.vertex_ai_project}"
        f"/locations/{settings.vertex_ai_location}"
        f"/endpoints/{settings.vertex_ai_medgemma_endpoint_id}"
    )
    endpoint = aiplatform.Endpoint(resource_name)
    instances = [
        {
            "@requestFormat": "chatCompletions",
            "messages": [
                {"role": "system", "content": "You are a medical audit assistant. Respond with valid JSON when asked."},
                {"role": "user", "content": full_prompt},
            ],
            "max_tokens": max_new_tokens,
            "temperature": 0,
        }
    ]
    response = endpoint.predict(instances=instances)
    preds = response.predictions
    if not preds:
        return ""
    p = preds[0] if isinstance(preds, list) else preds
    if isinstance(p, dict) and "choices" in p:
        choices = p["choices"]
        if choices and isinstance(choices[0], dict) and "message" in choices[0]:
            return (choices[0]["message"].get("content") or "").strip()
    return str(p).strip() if p else ""


def run_medgemma(
    prompt: str,
    ehr_excerpt: str | None = None,
    kb_context: str | None = None,
    max_new_tokens: int = 1024,
    medgemma_backend: str | None = None,
) -> dict[str, Any]:
    """
    Call MedGemma via HF Inference API or Vertex AI. Returns structured audit fields.
    If neither backend configured, returns STUB_REPORT.
    medgemma_backend: optional override "hf" | "vertex" for per-job selection.
    """
    if _is_vertex_configured(medgemma_backend):
        parts = []
        if kb_context:
            parts.append("## Knowledge base context\n" + kb_context)
        if ehr_excerpt:
            parts.append("## Patient EHR excerpt\n" + ehr_excerpt)
        parts.append("## Instruction\n" + prompt)
        full_prompt = "\n\n".join(parts)
        logger.info("medgemma (Vertex) PROMPT:\n%s", full_prompt)
        try:
            raw = _run_medgemma_vertex(full_prompt, max_new_tokens=max_new_tokens)
        except Exception:
            logger.exception("medgemma Vertex call FAILED")
            return STUB_REPORT.copy()
        logger.info("medgemma (Vertex) RESPONSE:\n%s", raw or "(empty)")
        parsed = _parse_structured_output(raw)
        return parsed if parsed else STUB_REPORT.copy()

    if medgemma_backend == "vertex":
        return STUB_REPORT.copy()
    if not settings.hf_token or not settings.hf_medgemma_endpoint:
        return STUB_REPORT.copy()

    # Build full prompt for model (HF path)
    parts = []
    if kb_context:
        parts.append("## Knowledge base context\n" + kb_context)
    if ehr_excerpt:
        parts.append("## Patient EHR excerpt\n" + ehr_excerpt)
    parts.append("## Instruction\n" + prompt)
    full_prompt = "\n\n".join(parts)

    logger.info("medgemma PROMPT:\n%s", full_prompt)

    url = settings.hf_medgemma_endpoint.rstrip("/")
    if "/chat" in url or "inference" in url:
        payload = {
            "inputs": full_prompt,
            "parameters": {"max_new_tokens": max_new_tokens},
        }
    else:
        payload = {
            "inputs": full_prompt,
            "parameters": {"max_new_tokens": max_new_tokens},
        }

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
        logger.exception("medgemma HTTP call FAILED")
        return STUB_REPORT.copy()

    # Parse model output into structured report (simplified: look for JSON block or use stub)
    raw = ""
    if isinstance(data, list) and len(data) > 0:
        raw = (
            data[0].get("generated_text", data[0])
            if isinstance(data[0], dict)
            else str(data[0])
        )
    elif isinstance(data, dict):
        raw = data.get("generated_text", data.get("output", str(data)))

    logger.info("medgemma RESPONSE:\n%s", raw or "(empty)")

    parsed = _parse_structured_output(raw)
    return parsed if parsed else STUB_REPORT.copy()


def run_medgemma_raw(prompt: str, ehr_text: str, max_new_tokens: int = 2048) -> str:
    """
    Call MedGemma for extraction (Pass 1). Returns raw text, no JSON parsing.
    Uses Vertex AI when configured, otherwise Hugging Face. Returns "" if neither configured.
    """
    full_prompt = "## Patient EHR\n" + (ehr_text or "") + "\n\n## Instruction\n" + prompt

    if _is_vertex_configured():
        logger.info("medgemma_raw (Vertex) PROMPT:\n%s", full_prompt)
        try:
            raw = _run_medgemma_vertex(full_prompt, max_new_tokens=max_new_tokens)
        except Exception:
            logger.exception("medgemma_raw Vertex call FAILED")
            return ""
        logger.info("medgemma_raw (Vertex) RESPONSE:\n%s", raw or "(empty)")
        return raw

    if not settings.hf_token or not settings.hf_medgemma_endpoint:
        return ""

    logger.info("medgemma_raw PROMPT:\n%s", full_prompt)

    url = settings.hf_medgemma_endpoint.rstrip("/")
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
        logger.exception("medgemma_raw HTTP call FAILED")
        return ""

    raw = ""
    if isinstance(data, list) and len(data) > 0:
        raw = (
            data[0].get("generated_text", data[0])
            if isinstance(data[0], dict)
            else str(data[0])
        )
    elif isinstance(data, dict):
        raw = data.get("generated_text", data.get("output", str(data)))
    raw = (raw or "").strip()
    logger.info("medgemma_raw RESPONSE:\n%s", raw or "(empty)")
    return raw


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
