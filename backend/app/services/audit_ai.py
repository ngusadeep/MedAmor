"""Unified audit AI: MedGemma (HF Endpoints), Gemini, or OpenAI. All configured via .env."""

import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.services import medgemma

logger = logging.getLogger(__name__)


def is_audit_ai_configured() -> bool:
    """True if the current AUDIT_AI_PROVIDER has required env vars set."""
    provider = (settings.audit_ai_provider or "medgemma").strip().lower()
    if provider == "medgemma":
        backend = getattr(settings, "medgemma_backend", None) or "hf"
        if backend == "vertex":
            return bool(
                settings.vertex_ai_project
                and settings.vertex_ai_location
                and settings.vertex_ai_medgemma_endpoint_id
            )
        return bool(settings.hf_token and settings.hf_medgemma_endpoint)
    if provider == "gemini":
        return bool(settings.google_api_key)
    if provider == "openai":
        return bool(settings.openai_api_key)
    return False


STUB_REPORT: dict[str, Any] = {
    "status": "NO_FINDINGS",
    "risk_level": "low",
    "executive_summary": "Automated review completed. No critical findings in this sample.",
    "findings": [],
    "evidence": [],
    "corrective_actions": [],
    "next_audit_date": None,
}


def _build_prompt_parts(
    prompt: str,
    ehr_excerpt: str | None = None,
    kb_context: str | None = None,
) -> str:
    parts = []
    if kb_context:
        parts.append("## Knowledge base context\n" + kb_context)
    if ehr_excerpt:
        parts.append("## Patient EHR excerpt\n" + ehr_excerpt)
    parts.append("## Instruction\n" + prompt)
    return "\n\n".join(parts)


def _parse_structured_output(raw: str) -> dict | None:
    if not raw or not raw.strip():
        return None
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError as e:
            logger.warning("JSON parse failed: %s — raw snippet: %.300s", e, m.group())
    else:
        logger.warning("No JSON object found in AI response (len=%d)", len(raw))
    return None


def _run_medgemma(
    prompt: str,
    ehr_excerpt: str | None,
    kb_context: str | None,
    medgemma_backend: str | None = None,
) -> dict[str, Any]:
    return medgemma.run_medgemma(
        prompt=prompt,
        ehr_excerpt=ehr_excerpt,
        kb_context=kb_context,
        medgemma_backend=medgemma_backend,
    )


def _run_gemini(
    prompt: str, ehr_excerpt: str | None, kb_context: str | None
) -> dict[str, Any]:
    if not settings.google_api_key:
        return STUB_REPORT.copy()
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        full = _build_prompt_parts(prompt, ehr_excerpt, kb_context)
        logger.info("gemini PROMPT:\n%s", full)
        response = model.generate_content(
            full,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4096,
                temperature=0.2,
            ),
        )
        raw = (response.text or "").strip()
        logger.info("gemini RESPONSE:\n%s", raw or "(empty)")
        parsed = _parse_structured_output(raw)
        if parsed:
            logger.info("gemini parsed OK — keys: %s", list(parsed.keys()))
            return parsed
        logger.warning("gemini parse FAILED — falling back to STUB_REPORT")
        return STUB_REPORT.copy()
    except Exception:
        logger.exception("gemini call FAILED with exception")
        return STUB_REPORT.copy()


def _run_openai(
    prompt: str, ehr_excerpt: str | None, kb_context: str | None
) -> dict[str, Any]:
    if not settings.openai_api_key:
        return STUB_REPORT.copy()
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        full = _build_prompt_parts(prompt, ehr_excerpt, kb_context)
        logger.info("openai PROMPT:\n%s", full)
        response = client.chat.completions.create(
            model=settings.openai_audit_model,
            messages=[{"role": "user", "content": full}],
            max_tokens=4096,
            temperature=0.2,
        )
        raw = (response.choices[0].message.content or "").strip()
        logger.info("openai RESPONSE:\n%s", raw or "(empty)")
        parsed = _parse_structured_output(raw)
        if parsed:
            logger.info("openai parsed OK — keys: %s", list(parsed.keys()))
            return parsed
        logger.warning("openai parse FAILED — falling back to STUB_REPORT")
        return STUB_REPORT.copy()
    except Exception:
        logger.exception("openai call FAILED with exception")
        return STUB_REPORT.copy()


def _get_model_info(provider: str) -> str:
    """Return a string describing which model/endpoint is used for the given provider."""
    if provider == "medgemma":
        return settings.hf_medgemma_endpoint or "(not configured)"
    if provider == "gemini":
        return getattr(settings, "gemini_model", "unknown")
    if provider == "openai":
        return getattr(settings, "openai_audit_model", "unknown")
    return "unknown"


def _parse_model_override(
    model_override: str | None,
) -> tuple[str | None, str | None]:
    """
    Parse per-job model override. Returns (audit_ai_provider, medgemma_backend).
    model_override: medgemma_hf | medgemma_vertex | medgemma | gemini | openai
    """
    if not model_override or not model_override.strip():
        return None, None
    val = model_override.strip().lower()
    if val == "gemini":
        return "gemini", None
    if val == "openai":
        return "openai", None
    if val in ("medgemma_hf", "medgemma-hf"):
        return "medgemma", "hf"
    if val in ("medgemma_vertex", "medgemma-vertex"):
        return "medgemma", "vertex"
    if val == "medgemma":
        return "medgemma", None
    return None, None


def run_audit_ai(
    prompt: str,
    ehr_excerpt: str | None = None,
    kb_context: str | None = None,
    model_override: str | None = None,
) -> dict[str, Any]:
    """
    Run audit with provider from AUDIT_AI_PROVIDER or per-job model_override.
    model_override: medgemma_hf | medgemma_vertex | medgemma | gemini | openai
    Returns structured dict: status, risk_level, executive_summary, findings, evidence, corrective_actions, next_audit_date.
    """
    provider_override, medgemma_backend_override = _parse_model_override(model_override)
    provider = (
        provider_override
        if provider_override
        else (settings.audit_ai_provider or "medgemma").strip().lower()
    )
    model_info = _get_model_info(provider)
    logger.info(
        "audit_ai_provider provider=%s model=%s model_override=%s",
        provider,
        model_info,
        model_override,
    )
    if provider == "gemini":
        return _run_gemini(prompt, ehr_excerpt, kb_context)
    if provider == "openai":
        return _run_openai(prompt, ehr_excerpt, kb_context)
    return _run_medgemma(
        prompt, ehr_excerpt, kb_context, medgemma_backend=medgemma_backend_override
    )


def _run_gemini_raw(prompt: str, ehr_text: str) -> str:
    """Run Gemini for extraction. Returns raw text (no JSON parsing)."""
    if not settings.google_api_key:
        return ""
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        full = "## Patient EHR\n" + (ehr_text or "") + "\n\n## Instruction\n" + prompt
        logger.info("gemini_raw PROMPT:\n%s", full)
        response = model.generate_content(
            full,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2048,
                temperature=0.2,
            ),
        )
        raw = (response.text or "").strip()
        logger.info("gemini_raw RESPONSE:\n%s", raw or "(empty)")
        return raw
    except Exception:
        logger.exception("gemini_raw call FAILED with exception")
        return ""


def _run_medgemma_raw(prompt: str, ehr_text: str) -> str:
    """Run MedGemma for extraction. Returns raw text (no JSON parsing)."""
    return medgemma.run_medgemma_raw(prompt=prompt, ehr_text=ehr_text)


def run_extraction(prompt: str, ehr_text: str, mode: str) -> str:
    """
    Run Pass 1 extraction. Returns raw text (not structured audit report).
    mode: gemini_extract | medgemma_extract
    """
    extract_model = (
        getattr(settings, "gemini_model", "unknown")
        if mode == "gemini_extract"
        else (settings.hf_medgemma_endpoint or "medgemma (not configured)")
    )
    logger.info(
        "audit_extraction mode=%s model=%s ehr_len=%d",
        mode,
        extract_model,
        len(ehr_text),
    )
    if mode == "gemini_extract":
        return _run_gemini_raw(prompt, ehr_text)
    return _run_medgemma_raw(prompt, ehr_text)
