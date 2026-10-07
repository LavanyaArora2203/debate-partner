# main.py  (project root)
# Run with: uvicorn main:app --reload --port 8000

import logging
import os
import time
from typing import Literal

try:
    from dotenv import load_dotenv
    # override=True: the .env file wins over a stale GROQ_API_KEY already set in
    # your shell or system environment. On Render there is no .env file, so this
    # does nothing there and the dashboard environment variables are used.
    load_dotenv(override=True)
except ImportError:
    pass

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.judge import judge_speech
from core.llm import LLMAuthError, LLMError, call_llm, key_diagnostics
from core.opponent import generate_rebuttal
from core.schemas import Feedback
from core.transcribe import transcribe_audio_bytes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("debate-partner")

MAX_AUDIO_BYTES = 10 * 1024 * 1024   # 10 MB (about 3 minutes of webm audio is far smaller)
MIN_WORDS = 30
MAX_WORDS = 600

# Safe startup log: shows whether the key was found, never the key itself.
log.info("GROQ_API_KEY diagnostics: %s", key_diagnostics())

app = FastAPI(title="Debate Partner API", version="0.1.0")

# Comma-separated list in .env, e.g. ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()]
log.info("CORS allowed origins: %s", origins)
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


@app.get("/health/llm")
def health_llm() -> dict:
    """Makes one tiny Groq call so you can test the key on the deployed server.
    Visit /health/llm in a browser. Returns no secrets. Remove it when you're done debugging."""
    diag = key_diagnostics()
    try:
        call_llm(system="Reply with the single word: ok", user="ping", max_tokens=200, temperature=0.0)
    except LLMAuthError:
        return {"status": "key_rejected_or_missing", "key": diag}
    except LLMError:
        log.exception("LLM health check failed")
        return {"status": "llm_error_see_server_logs", "key": diag}
    return {"status": "ok", "key": diag}


@app.post("/debate", response_model=DebateResponse)
def debate(req: DebateRequest) -> DebateResponse:
    words = len(req.speech.split())
    if words < MIN_WORDS:
        raise HTTPException(400, f"Speech is too short. Please write at least {MIN_WORDS} words.")
    if words > MAX_WORDS:
        raise HTTPException(400, f"Speech is too long. Please keep it under {MAX_WORDS} words.")

    t0 = time.perf_counter()

    # Opponent and judge are separate steps so the logs say which one failed.
    try:
        rebuttal = generate_rebuttal(req.motion, req.student_side, req.speech, req.level)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except LLMAuthError:
        log.exception("Opponent step: API key problem")
        raise HTTPException(503, "The service is temporarily unavailable. Please try again later.")
    except LLMError:
        log.exception("Opponent step failed")
        raise HTTPException(502, "The AI opponent had trouble responding. Please try again.")
    except Exception:
        log.exception("Unexpected error in opponent step")
        raise HTTPException(500, "Something went wrong. Please try again.")

    try:
        feedback = judge_speech(req.motion, req.student_side, req.speech, rebuttal)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except LLMAuthError:
        log.exception("Judge step: API key problem")
        raise HTTPException(503, "The service is temporarily unavailable. Please try again later.")
    except RuntimeError:  # LLMError or invalid judge JSON after retry
        log.exception("Judge step failed")
        raise HTTPException(502, "The judge had trouble responding. Please try again.")
    except Exception:
        log.exception("Unexpected error in judge step")
        raise HTTPException(500, "Something went wrong. Please try again.")

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