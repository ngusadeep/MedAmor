"""Transcription service: MedASR (HuggingFace API), MedASR Local, and Deepgram.

Providers
---------
medasr        – MedASR via HuggingFace Inference API (remote, requires HF_TOKEN +
                MEDASR_HF_ENDPOINT).
medasr_local  – google/medasr loaded locally via transformers >= 5.0.0.
                Requires: transformers>=5.0.0, torch, librosa, ffmpeg (system).
                Model card: https://huggingface.co/google/medasr
deepgram      – Deepgram Nova-2-Medical REST API (requires DEEPGRAM_API_KEY).

Audio decoding for local inference
------------------------------------
Browser MediaRecorder emits audio/webm;codecs=opus.  librosa.load() handles the
conversion to 16 kHz float32 mono internally via audioread + ffmpeg.
ffmpeg must be installed (see Dockerfile).
"""

import logging
import os
import tempfile
import threading
from typing import TYPE_CHECKING

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local MedASR – lazy singleton (processor + model), thread-safe
# We use AutoProcessor + AutoModelForCTC instead of the ASR pipeline to avoid
# a transformers 5.2 bug where the pipeline passes an extra "center" argument
# to LasrFeatureExtractor._torch_extract_fbank_features() (TypeError: 4 given, 2-3 expected).
# Model card: https://huggingface.co/google/medasr
# ---------------------------------------------------------------------------

_local_processor = None
_local_model = None
_local_model_id: str | None = None
_pipeline_lock = threading.Lock()


def _patch_lasr_feature_extractor() -> None:
    """Monkey-patch LasrFeatureExtractor for transformers 5.2.x compatibility.

    In transformers 5.2.0 the __call__ method passes a `center` positional arg
    to _torch_extract_fbank_features, but the method signature only accepts
    (self, waveform, device).  This was fixed in main but not yet released.
    The patch wraps the method to silently absorb the extra argument.
    """
    try:
        import inspect
        from transformers.models.lasr.feature_extraction_lasr import LasrFeatureExtractor

        sig = inspect.signature(LasrFeatureExtractor._torch_extract_fbank_features)
        if "center" not in sig.parameters:
            _orig = LasrFeatureExtractor._torch_extract_fbank_features

            def _patched(self, waveform, device="cpu", center=None, **kw):  # noqa: ANN001
                return _orig(self, waveform, device)

            LasrFeatureExtractor._torch_extract_fbank_features = _patched  # type: ignore[method-assign]
            logger.info("Applied LasrFeatureExtractor patch (transformers 5.2.x compat)")
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not apply LasrFeatureExtractor patch: %s", exc)


def _load_local_medasr() -> tuple:
    """Load (and cache) processor and model for google/medasr.

    Returns (processor, model). Uses AutoProcessor + AutoModelForCTC per the
    model card. Also applies a one-time patch for transformers 5.2.x.
    """
    global _local_processor, _local_model, _local_model_id
    if _local_processor is not None and _local_model is not None:
        return _local_processor, _local_model

    with _pipeline_lock:
        if _local_processor is not None and _local_model is not None:
            return _local_processor, _local_model

        from transformers import AutoModelForCTC, AutoProcessor

        # Patch the LASR feature extractor before loading so any internal
        # call to _torch_extract_fbank_features gets the correct signature.
        _patch_lasr_feature_extractor()

        model_id = settings.medasr_local_model or "google/medasr"
        device = settings.medasr_local_device or "cpu"

        logger.info("Loading local ASR model '%s' on device '%s'…", model_id, device)
        _local_processor = AutoProcessor.from_pretrained(model_id)
        _local_model = AutoModelForCTC.from_pretrained(model_id).to(device)
        _local_model_id = model_id
        logger.info("Local ASR model loaded: %s", model_id)

    return _local_processor, _local_model


def _decode_audio_with_librosa(audio_bytes: bytes, content_type: str):
    """Convert audio bytes to 16 kHz float32 mono numpy array using librosa.

    librosa.load() normalises to float32, resamples to 16 kHz, and mixes down
    to mono in one call.  For webm/opus it falls back to audioread which uses
    ffmpeg under the hood (requires ffmpeg installed in the container).

    Returns:
        (numpy.ndarray, int) – (audio_array float32, 16000)
    """
    import librosa

    # Determine file extension so ffmpeg/audioread picks the right demuxer
    if "webm" in content_type:
        ext = ".webm"
    elif "ogg" in content_type:
        ext = ".ogg"
    elif "mp4" in content_type or "m4a" in content_type:
        ext = ".mp4"
    elif "wav" in content_type:
        ext = ".wav"
    elif "mpeg" in content_type or "mp3" in content_type:
        ext = ".mp3"
    else:
        ext = ".webm"  # best guess for browser recordings

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # sr=16000: resample to 16 kHz (MedASR requirement)
        # mono=True: mix down to mono
        audio_array, sample_rate = librosa.load(tmp_path, sr=16000, mono=True)
    finally:
        os.unlink(tmp_path)

    return audio_array, sample_rate


def _ctc_collapse(ids: list[int]) -> list[int]:
    """Apply CTC post-processing: collapse consecutive identical token IDs.

    CTC output is a sequence of per-frame labels where the same label repeated
    across adjacent frames means a single emitted token (not two identical ones).
    This step must happen *before* the tokenizer decodes IDs into text, because
    the tokenizer has no knowledge of which IDs are CTC duplicates vs. genuinely
    separate tokens.
    """
    import itertools
    # groupby keeps the first element of each run of identical values
    return [k for k, _ in itertools.groupby(ids)]


def _run_local_inference(audio_bytes: bytes, content_type: str) -> str:
    """Synchronous local inference: decode → CTC logits → greedy argmax → transcript.

    CTC decoding pipeline:
      1. logits  = model(**inputs).logits       (batch, time, vocab)
      2. ids     = argmax(logits, dim=-1)        greedy label per frame
      3. ids     = _ctc_collapse(ids)            collapse consecutive duplicates
      4. text    = tokenizer.decode(ids, skip_special_tokens=True)
                                                 remove blank / EOS tokens

    The LASR tokenizer does not apply step 3 internally, so we must do it
    before calling decode, otherwise each CTC emission becomes a repeated
    word (e.g. "so so so", "goinging", "inffforormmmation").

    Runs in a thread-pool executor (called via asyncio.run_in_executor).
    """
    import numpy as np
    import torch

    audio_array, sample_rate = _decode_audio_with_librosa(audio_bytes, content_type)
    speech = np.asarray(audio_array, dtype=np.float32)

    processor, model = _load_local_medasr()
    device = settings.medasr_local_device or "cpu"

    inputs = processor(
        speech,
        sampling_rate=sample_rate,
        return_tensors="pt",
        padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits  # (batch, time, vocab)

    predicted_ids = torch.argmax(logits, dim=-1)  # (batch, time)

    # Apply CTC collapse per sequence, then decode
    results: list[str] = []
    for seq in predicted_ids:
        collapsed = _ctc_collapse(seq.tolist())
        text = processor.tokenizer.decode(collapsed, skip_special_tokens=True)
        results.append(text.strip())

    return results[0] if results else ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def transcribe_audio(
    audio_bytes: bytes,
    content_type: str,
    provider: str | None = None,
) -> str:
    """Transcribe audio bytes to text.

    Args:
        audio_bytes: Raw audio data (webm, mp4, wav, …).
        content_type: MIME type of the audio (e.g. ``"audio/webm"``).
        provider: Override – ``"medasr"``, ``"medasr_local"``, or ``"deepgram"``.
                  Falls back to ``settings.asr_provider``.

    Returns:
        Transcript string (may be empty if audio contained no speech).

    Raises:
        RuntimeError: Requested provider is not configured.
        httpx.HTTPStatusError: Upstream API returned an error.
    """
    chosen = (provider or settings.asr_provider or "medasr").lower()

    if chosen == "deepgram":
        return await _transcribe_deepgram(audio_bytes, content_type)
    if chosen == "medasr_local":
        return await _transcribe_medasr_local(audio_bytes, content_type)
    return await _transcribe_medasr(audio_bytes, content_type)


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


async def _transcribe_medasr(audio_bytes: bytes, content_type: str) -> str:
    """Call MedASR via HuggingFace Inference API (remote)."""
    if not settings.hf_token:
        raise RuntimeError(
            "MedASR not configured: set HF_TOKEN in .env "
            "(same token used for MedGemma)"
        )
    if not settings.medasr_hf_endpoint:
        raise RuntimeError(
            "MedASR not configured: set MEDASR_HF_ENDPOINT in .env "
            "(e.g. https://api-inference.huggingface.co/models/google/medasr)"
        )

    url = settings.medasr_hf_endpoint.rstrip("/")
    headers = {
        "Authorization": f"Bearer {settings.hf_token}",
        "Content-Type": content_type,
    }

    logger.info("MedASR (API) request: %d bytes → %s", len(audio_bytes), url)

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, content=audio_bytes, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    logger.info("MedASR (API) response: %s", data)

    if isinstance(data, dict):
        return (data.get("text") or data.get("transcription") or "").strip()
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return (first.get("text") or first.get("transcription") or "").strip()
    return str(data).strip()


async def _transcribe_medasr_local(audio_bytes: bytes, content_type: str) -> str:
    """Run google/medasr locally via AutoProcessor + AutoModelForCTC.

    Model inference is CPU-bound, so we offload it to a thread-pool executor to
    avoid blocking the async event loop.

    Requirements (see pyproject.toml):
      transformers>=5.0.0  torch  librosa  ffmpeg (system package)
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        text: str = await loop.run_in_executor(
            None, _run_local_inference, audio_bytes, content_type
        )
        logger.info(
            "MedASR (local, model=%s) → %r",
            settings.medasr_local_model,
            text[:120],
        )
        return text
    except ImportError as exc:
        raise RuntimeError(
            f"Local ASR dependencies missing ({exc}). "
            "Install: transformers>=5.0.0 torch librosa; "
            "and ensure ffmpeg is available."
        ) from exc


async def _transcribe_deepgram(audio_bytes: bytes, content_type: str) -> str:
    """Call Deepgram Nova-2-Medical ASR API."""
    if not settings.deepgram_api_key:
        raise RuntimeError(
            "Deepgram not configured: set DEEPGRAM_API_KEY in .env"
        )

    headers = {
        "Authorization": f"Token {settings.deepgram_api_key}",
        "Content-Type": content_type,
    }
    params = {
        "model": "nova-3-medical",
        "smart_format": "true",
        "punctuate": "true",
        "diarize": "false",
        "language": "en",
    }

    logger.info(
        "Deepgram request: %d bytes, content-type=%s", len(audio_bytes), content_type
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.deepgram.com/v1/listen",
            content=audio_bytes,
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    logger.info("Deepgram response metadata: %s", data.get("metadata"))

    try:
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        return transcript.strip()
    except (KeyError, IndexError):
        logger.warning("Deepgram: unexpected response shape: %s", data)
        return ""
