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

if TYPE_CHECKING:
    from transformers import Pipeline  # noqa: F401

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local pipeline – lazy singleton, thread-safe
# ---------------------------------------------------------------------------

_local_pipeline: "Pipeline | None" = None
_pipeline_lock = threading.Lock()


def _load_local_pipeline() -> "Pipeline":
    """Load (and cache) the local HuggingFace ASR pipeline.

    Called from a thread-pool executor so it never blocks the async event loop.
    Double-checked locking ensures the model is loaded exactly once even under
    concurrent requests.

    Uses google/medasr per the model card:
      pipe = pipeline("automatic-speech-recognition", model="google/medasr")
    """
    global _local_pipeline
    if _local_pipeline is not None:
        return _local_pipeline

    with _pipeline_lock:
        if _local_pipeline is not None:
            return _local_pipeline

        from transformers import pipeline as hf_pipeline

        model_id = settings.medasr_local_model or "google/medasr"
        device = settings.medasr_local_device or "cpu"

        logger.info("Loading local ASR model '%s' on device '%s'…", model_id, device)
        _local_pipeline = hf_pipeline(
            "automatic-speech-recognition",
            model=model_id,
            device=device,
        )
        logger.info("Local ASR model loaded: %s", model_id)

    return _local_pipeline


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


def _run_local_inference(audio_bytes: bytes, content_type: str) -> str:
    """Synchronous local inference: decode → pipeline → transcript.

    Matches the usage shown in the MedASR model card:
      result = pipe(audio, chunk_length_s=20, stride_length_s=2)

    Runs in a thread-pool executor (called via asyncio.run_in_executor).
    """
    audio_array, sample_rate = _decode_audio_with_librosa(audio_bytes, content_type)

    pipe = _load_local_pipeline()

    # chunk_length_s=20, stride_length_s=2 per the google/medasr model card
    result = pipe(
        {"array": audio_array, "sampling_rate": sample_rate},
        chunk_length_s=20,
        stride_length_s=2,
    )

    if isinstance(result, dict):
        return (result.get("text") or "").strip()
    if isinstance(result, list) and result:
        first = result[0]
        return (first.get("text") or "" if isinstance(first, dict) else str(first)).strip()
    return str(result).strip()


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
    """Run google/medasr locally via transformers pipeline.

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
