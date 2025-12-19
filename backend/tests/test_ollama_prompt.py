"""
Simple prompt smoke test for the local Ollama model.
Run with:
    python backend/tests/test_ollama_prompt.py
"""

from __future__ import annotations
import os
import sys
from typing import Any, Dict

try:
    import ollama
except ImportError:
    sys.stderr.write(
        "ollama package is not installed. Activate pvenv and run:\n"
        "    pip install -r extras/requirements.txt\n"
    )
    raise


def run_prompt(prompt: str, model: str, host: str | None = None, stream: bool = False) -> Dict[str, Any]:
    """
    Send a single prompt to the configured Ollama model.
    Supports both streaming and non-streaming.
    """

    # Resolve host settings
    client_host = host or os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST")
    if client_host:
        os.environ["OLLAMA_HOST"] = client_host

    print(f"👉 Sending prompt to model '{model}' at {os.getenv('OLLAMA_HOST', 'default host')}...\n")

    try:
        if stream:
            # STREAMING MODE – immediate output
            response_stream = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            print("🔵 Streaming response:\n")
            final_message = ""

            for chunk in response_stream:
                content = chunk.get("message", {}).get("content", "")
                final_message += content
                print(content, end="", flush=True)

            print("\n\n✅ Stream complete.")
            return {"message": {"content": final_message}}

        else:
            # NON-STREAMING MODE – waits for full output
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            return response

    except ollama.ResponseError as err:
        print(f"❌ Ollama error: {err}")
        sys.exit(1)


def main() -> None:
    prompt = "what do you know by APJ Abdul Kalam ?, an  give me a response in 2 sentence."

    # Default model → use your installed one
    model_name = os.getenv("OLLAMA_MODEL_NAME", "mistral:latest")
    host = os.getenv("OLLAMA_BASE_URL")

    # 👉 Change stream=True to get instant output even on slow CPU models
    payload = run_prompt(prompt, model=model_name, host=host, stream=True)

    message = payload.get("message", {}).get("content", "").strip()
    if not message:
        print("⚠️ Ollama returned no content:", payload)
        sys.exit(1)

    print("\n\n🟢 Final model reply:\n")
    print(message)


if __name__ == "__main__":
    main()
