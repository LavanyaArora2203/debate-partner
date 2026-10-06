import os
from openai import OpenAI

MODEL = os.getenv("LLM_MODEL", "gpt-6-luna")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def call_llm(
    system: str,
    user: str,
    max_tokens: int = 900,
    temperature: float = 0.8,
    json_mode: bool = False,
) -> str:

    kwargs = {
        "model": MODEL,
        "instructions": system,
        "input": user,
        "max_output_tokens": max_tokens,
        "temperature": temperature,
    }

    if json_mode:
        kwargs["text"] = {
            "format": {
                "type": "json_object"
            }
        }

    response = client.responses.create(**kwargs)

    return response.output_text