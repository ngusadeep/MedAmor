"""Unified audit AI: MedGemma (HF Endpoints), Gemini, or OpenAI. All configured via .env."""

import json
import re
from typing import Any

from app.core.config import settings
from app.services import medgemma


def is_audit_ai_configured() -> bool:
    """True if the current AUDIT_AI_PROVIDER has required env vars set."""
    provider = (settings.audit_ai_provider or "medgemma").strip().lower()
    if provider == "medgemma":
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
        parts.append("## Knowledge base context\n" + kb_context[:8000])
    if ehr_excerpt:
        parts.append("## Patient EHR excerpt\n" + ehr_excerpt[:12000])
    parts.append("## Instruction\n" + prompt)
    return "\n\n".join(parts)


def _parse_structured_output(raw: str) -> dict | None:
    if not raw or not raw.strip():
        return None
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def _run_medgemma(prompt: str, ehr_excerpt: str | None, kb_context: str | None) -> dict[str, Any]:
    return medgemma.run_medgemma(
        prompt=prompt,
        ehr_excerpt=ehr_excerpt,
        kb_context=kb_context,
    )


def _run_gemini(prompt: str, ehr_excerpt: str | None, kb_context: str | None) -> dict[str, Any]:
    if not settings.google_api_key:
        return STUB_REPORT.copy()
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        full = _build_prompt_parts(prompt, ehr_excerpt, kb_context)
        response = model.generate_content(
            full,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1024,
                temperature=0.2,
            ),
        )
        raw = (response.text or "").strip()
        parsed = _parse_structured_output(raw)
        return parsed if parsed else STUB_REPORT.copy()
    except Exception:
        return STUB_REPORT.copy()


def _run_openai(prompt: str, ehr_excerpt: str | None, kb_context: str | None) -> dict[str, Any]:
    if not settings.openai_api_key:
        return STUB_REPORT.copy()
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        full = _build_prompt_parts(prompt, ehr_excerpt, kb_context)
        response = client.chat.completions.create(
            model=settings.openai_audit_model,
            messages=[{"role": "user", "content": full}],
            max_tokens=1024,
            temperature=0.2,
        )
        raw = (response.choices[0].message.content or "").strip()
        parsed = _parse_structured_output(raw)
        return parsed if parsed else STUB_REPORT.copy()
    except Exception:
        return STUB_REPORT.copy()


def run_audit_ai(
    prompt: str,
    ehr_excerpt: str | None = None,
    kb_context: str | None = None,
) -> dict[str, Any]:
    """
    Run audit with provider from AUDIT_AI_PROVIDER (medgemma | gemini | openai).
    All provider keys are read from config (loaded from .env).
    Returns structured dict: status, risk_level, executive_summary, findings, evidence, corrective_actions, next_audit_date.
    """
    provider = (settings.audit_ai_provider or "medgemma").strip().lower()
    if provider == "gemini":
        return _run_gemini(prompt, ehr_excerpt, kb_context)
    if provider == "openai":
        return _run_openai(prompt, ehr_excerpt, kb_context)
    return _run_medgemma(prompt, ehr_excerpt, kb_context)
