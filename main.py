# main.py  (project root)
# Run with: uvicorn main:app --reload --port 8000

import logging
import os
import time
from typing import Literal

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.judge import judge_speech
from core.opponent import generate_rebuttal
from core.schemas import Feedback
from core.transcribe import transcribe_audio_bytes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("debate-partner")

MAX_AUDIO_BYTES = 10 * 1024 * 1024   # 10 MB (about 3 minutes of webm audio is far smaller)
MIN_WORDS = 30
MAX_WORDS = 600

app = FastAPI(title="Debate Partner API", version="0.1.0")

# Comma-separated list in .env, e.g. ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ---------- Schemas ----------

class DebateRequest(BaseModel):
    motion: str = Field(min_length=5, max_length=300)
    student_side: Literal["Proposition", "Opposition"]
    level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    speech: str = Field(min_length=1, max_length=6000)


class DebateResponse(BaseModel):
    rebuttal: str
    feedback: Feedback


class TranscribeResponse(BaseModel):
    text: str


# ---------- Routes ----------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/debate", response_model=DebateResponse)
def debate(req: DebateRequest) -> DebateResponse:
    words = len(req.speech.split())
    if words < MIN_WORDS:
        raise HTTPException(400, f"Speech is too short. Please write at least {MIN_WORDS} words.")
    if words > MAX_WORDS:
        raise HTTPException(400, f"Speech is too long. Please keep it under {MAX_WORDS} words.")

    t0 = time.perf_counter()
    try:
        rebuttal = generate_rebuttal(req.motion, req.student_side, req.speech, req.level)
        feedback = judge_speech(req.motion, req.student_side, req.speech, rebuttal)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        log.exception("Judge failed")
        raise HTTPException(502, detail=str(e))
    except Exception as e:
        log.exception("Unexpected error in /debate")
        raise HTTPException(500, detail=str(e))

    # Log metrics only, never the speech text (users may be minors)
    log.info("debate ok | level=%s | words=%d | %.1fs", req.level, words, time.perf_counter() - t0)
    return DebateResponse(rebuttal=rebuttal, feedback=feedback)


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile = File(...)) -> TranscribeResponse:
    data = await audio.read()
    if not data:
        raise HTTPException(400, "No audio received.")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Recording is too large. Please keep it under 3 minutes.")

    suffix = ".mp4" if "mp4" in (audio.content_type or "") else ".webm"  # Safari records mp4

    t0 = time.perf_counter()
    try:
        text = transcribe_audio_bytes(data, suffix=suffix)
    except Exception:
        log.exception("Transcription failed")
        raise HTTPException(500, "Could not transcribe the recording. Please try again or type your speech.")

    if not text:
        raise HTTPException(422, "We couldn't hear any speech. Please check your microphone and try again.")

    log.info("transcribe ok | %d bytes | %.1fs", len(data), time.perf_counter() - t0)
    return TranscribeResponse(text=text)