# core/llm.py
import logging
import os
import time

from groq import (
    APIConnectionError,
    APIError,
    APIStatusError,
    AuthenticationError,
    Groq,
    PermissionDeniedError,
    RateLimitError,
)

log = logging.getLogger("debate-partner.llm")

PRIMARY_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b").strip()
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "openai/gpt-oss-120b").strip()
REQUEST_TIMEOUT_S = 30


class LLMError(RuntimeError):
    """Any failure talking to the LLM provider."""


class LLMAuthError(LLMError):
    """The API key is missing, malformed, or rejected by Groq."""


_client: Groq | None = None


def _read_api_key() -> str:
    # Strip whitespace and accidental quotes (a very common .env mistake).
    key = os.environ.get("GROQ_API_KEY", "").strip().strip("\"'").strip()
    if not key:
        raise LLMAuthError("GROQ_API_KEY is not set in the environment.")
    return key


def key_diagnostics() -> dict:
    """Safe-to-log facts about the key. Never returns the key itself."""
    raw = os.environ.get("GROQ_API_KEY", "")
    key = raw.strip().strip("\"'").strip()
    return {
        "set": bool(key),
        "length": len(key),
        "starts_with_gsk_": key.startswith("gsk_"),
        "had_whitespace_or_quotes": raw != key,
    }


def _get_client() -> Groq:
    # Created lazily so the app can boot (and /health works) even if the key is
    # wrong, and so load_dotenv() has always run before we read the key.
    global _client
    if _client is None:
        # max_retries=0: we do our own retrying below, so retries don't multiply.
        _client = Groq(api_key=_read_api_key(), timeout=REQUEST_TIMEOUT_S, max_retries=0)
    return _client


def call_llm(
    system: str,
    user: str,
    max_tokens: int = 500,
    temperature: float = 0.7,
    json_mode: bool = False,
    max_retries: int = 3,
) -> str:
    """Calls Groq with retries and a model fallback. Always returns non-empty text
    or raises LLMError (LLMAuthError for key problems)."""

    client = _get_client()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    models = [PRIMARY_MODEL]
    if FALLBACK_MODEL and FALLBACK_MODEL != PRIMARY_MODEL:
        models.append(FALLBACK_MODEL)

    last_error: Exception | None = None

    for model in models:
        for attempt in range(max_retries):
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_completion_tokens": max_tokens,
                "stream": False,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            if "gpt-oss" in model:
                # Reasoning tokens count against max_completion_tokens. Keeping
                # effort low stops the model from using the whole budget thinking
                # and returning empty or truncated output.
                kwargs["extra_body"] = {"reasoning_effort": "low"}

            try:
                response = client.chat.completions.create(**kwargs)
            except (AuthenticationError, PermissionDeniedError) as e:
                # Retrying a rejected key can never help. Fail now with a clear message.
                log.error("Groq rejected the API key (HTTP %s).", e.status_code)
                raise LLMAuthError(
                    f"Groq rejected the API key (HTTP {e.status_code}). "
                    "Check GROQ_API_KEY for typos, quotes, stale copies, or revocation."
                ) from e
            except RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                log.warning("Rate limited on %s (attempt %d/%d). Waiting %ds.", model, attempt + 1, max_retries, wait)
                time.sleep(wait)
                continue
            except APIConnectionError as e:  # includes timeouts
                last_error = e
                wait = 2 ** attempt
                log.warning("Connection problem on %s: %s. Waiting %ds.", model, e, wait)
                time.sleep(wait)
                continue
            except APIStatusError as e:
                last_error = e
                if e.status_code >= 500:
                    wait = 2 ** attempt
                    log.warning("Groq %s error on %s. Waiting %ds.", e.status_code, model, wait)
                    time.sleep(wait)
                    continue
                # Other 4xx (bad request, unknown model, ...): retrying the same
                # request is pointless. Try the next model.
                log.error("Groq %s error on %s: %s", e.status_code, model, e)
                break
            except APIError as e:
                last_error = e
                log.error("Groq API error on %s: %s", model, e)
                break
            except Exception as e:
                last_error = e
                log.exception("Unexpected error calling %s", model)
                break

            choice = response.choices[0]
            content = (choice.message.content or "").strip()
            if content and choice.finish_reason != "length":
                return content

            # Empty or truncated output. Same request will fail the same way,
            # so move on to the fallback model.
            last_error = LLMError(
                f"{model} returned {'empty' if not content else 'truncated'} output "
                f"(finish_reason={choice.finish_reason}). Try raising max_tokens."
            )
            log.warning("%s", last_error)
            break

    raise LLMError(f"All models failed. Last error: {last_error}")