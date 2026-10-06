import os
import time
from groq import Groq
from groq import RateLimitError, APIError

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set.")

client = Groq(api_key=GROQ_API_KEY)

PRIMARY_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
FALLBACK_MODEL = "openai/gpt-oss-120b"


def call_llm(
    system: str,
    user: str,
    max_tokens: int = 500,
    temperature: float = 0.7,
    json_mode: bool = False,
    max_retries: int = 3
) -> str:

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

    last_error = None

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:

        for attempt in range(max_retries):

            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_completion_tokens": max_tokens,
                    "stream": False,
                }

                if json_mode:
                    kwargs["response_format"] = {
                        "type": "json_object"
                    }

                response = client.chat.completions.create(**kwargs)

                return response.choices[0].message.content

            except RateLimitError as e:
                last_error = e
                wait_time = 2 ** attempt
                print(
                    f"Rate limit reached for {model}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

            except APIError as e:
                last_error = e
                print(f"Groq API error with {model}: {e}")
                time.sleep(2 ** attempt)

            except Exception as e:
                last_error = e
                print(f"Unexpected error with {model}: {e}")
                break

    raise RuntimeError(
        f"All Groq models failed. Last error: {last_error}"
    )