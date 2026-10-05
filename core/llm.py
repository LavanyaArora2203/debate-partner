import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"


def call_llm(
    system: str,
    user: str,
    max_tokens: int = 900,
    temperature: float = 0.8,
) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": user,
                },
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        },
    )

    response.raise_for_status()

    return response.json()["message"]["content"]