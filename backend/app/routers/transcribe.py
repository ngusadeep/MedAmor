"""Transcription endpoint: POST /transcribe

Accepts a multipart audio upload and returns the transcript text.
Providers:
  medasr        – MedASR via HuggingFace Inference API (remote)
  medasr_local  – local HuggingFace pipeline (transformers + torch)
  deepgram      – Deepgram Nova-2-Medical API
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.deps import get_current_user_required
from app.models.user import User
from app.services.transcription import transcribe_audio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcribe", tags=["transcribe"])


class TranscribeResponse(BaseModel):
    text: str
    provider: str


@router.post("", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(..., description="Audio recording (webm, mp4, wav)"),
    provider: str = Form(
        default="medasr",
        description="ASR provider: 'medasr' | 'medasr_local' | 'deepgram'",
    ),
    _user: User = Depends(get_current_user_required),
) -> TranscribeResponse:
    """Transcribe a clinical voice note to text.

    Multipart form fields:
    - audio: audio file (browser MediaRecorder output, typically audio/webm)
    - provider: "medasr" | "medasr_local" | "deepgram"  (default: "medasr")

    Returns the transcript and the provider used.
    """
    if provider not in ("medasr", "medasr_local", "deepgram"):
        raise HTTPException(
            status_code=422,
            detail="provider must be 'medasr', 'medasr_local', or 'deepgram'",
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Audio file is empty")

    content_type = audio.content_type or "audio/webm"

    try:
        text = await transcribe_audio(audio_bytes, content_type, provider=provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Transcription failed (provider=%s)", provider)
        raise HTTPException(status_code=500, detail="Transcription service error")

    logger.info(
        "Transcribed %d bytes via %s → %d chars",
        len(audio_bytes),
        provider,
        len(text),
    )
    return TranscribeResponse(text=text, provider=provider)
