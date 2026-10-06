# import os
# from openai import OpenAI

# MODEL = os.getenv("LLM_MODEL", "gpt-6-luna")

# client = OpenAI(
#     api_key=os.getenv("OPENAI_API_KEY")
# )


# def call_llm(
#     system: str,
#     user: str,
#     max_tokens: int = 900,
#     temperature: float = 0.8,
#     json_mode: bool = False,
# ) -> str:

#     kwargs = {
#         "model": MODEL,
#         "instructions": system,
#         "input": user,
#         "max_output_tokens": max_tokens,
#         "temperature": temperature,
#     }

#     if json_mode:
#         kwargs["text"] = {
#             "format": {
#                 "type": "json_object"
#             }
#         }

#     response = client.responses.create(**kwargs)

#     return response.output_text
import os, requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")

def call_llm(system: str, user: str, max_tokens: int = 900,
             temperature: float = 0.8, json_mode: bool = False) -> str:
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens, "num_ctx": 4096},
    }
    if json_mode:
        payload["format"] = "json"
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"]