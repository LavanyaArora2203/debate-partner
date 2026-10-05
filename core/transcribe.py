# core/transcribe.py
import os
import tempfile
from functools import lru_cache

from faster_whisper import WhisperModel

MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")  # "base" is faster, "small" handles accents better


@lru_cache(maxsize=1)
def _get_model() -> WhisperModel:
    # Loaded once on first use, then reused. int8 keeps CPU usage and memory low.
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio_bytes(audio_bytes: bytes, suffix: str = ".webm") -> str:
    """Transcribes audio and discards it. Nothing is stored."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        segments, _info = _get_model().transcribe(
            tmp_path,
            language="en",
            vad_filter=True,   # skips long silences
            beam_size=5,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)