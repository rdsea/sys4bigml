"""LLM backend for the agent service.

One backend behind one interface, ``complete(prompt) -> str``:

- ``OllamaLLM`` — real local inference via an Ollama server (set OLLAMA_HOST,
  OLLAMA_PORT and OLLAMA_MODEL in the environment).

The backend tracks ``calls`` / ``prompt_tokens`` / ``completion_tokens`` the
way an API bill would.

Optional: if LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST are
set (see README), every completion is also logged to Langfuse as a
generation via ``log_generation``.
"""
import os

import requests


class OllamaLLM:
    """Real local inference through Ollama's /api/generate endpoint."""

    def __init__(self, host, port, model):
        self.base = f"http://{host}:{port}"
        self.model = model
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def complete(self, prompt):
        self.calls += 1
        self.prompt_tokens += len(prompt) // 4
        resp = requests.post(f"{self.base}/api/generate",
                             json={"model": self.model, "prompt": prompt,
                                   "stream": False},
                             timeout=120)
        resp.raise_for_status()
        out = resp.json().get("response", "")
        self.completion_tokens += len(out) // 4
        return out


def get_llm():
    """The configured OllamaLLM. Inference is a hard dependency: a missing
    host or model is a configuration error, not something to paper over with
    a stand-in that would quietly teach the wrong failure statistics."""
    host = os.getenv("OLLAMA_HOST") or ""
    model = os.getenv("OLLAMA_MODEL") or ""
    if not (host and model):
        raise RuntimeError(
            "OLLAMA_HOST and OLLAMA_MODEL must be set — install Ollama "
            "(https://ollama.com), pull a model (e.g. `ollama pull llama3.2`) "
            "and set them in .env (see .env.example).")
    return OllamaLLM(host, os.getenv("OLLAMA_PORT") or "11434", model)


# --- Optional Langfuse logging ------------------------------------------------

def get_langfuse():
    """A Langfuse client when keys are configured, else None."""
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        return None
    try:
        from langfuse import Langfuse
        return Langfuse(public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"))
    except Exception:
        return None


_langfuse_warned = False


def log_generation(client, name, prompt, output, model):
    """One completion -> one Langfuse generation event (no-op without client).

    The SDK renamed this call: v3 had ``start_generation``, v4 replaced it with
    ``start_observation(as_type="generation")``. Both are supported here — an
    SDK upgrade should not silently switch LLM logging off.
    """
    if client is None:
        return
    global _langfuse_warned
    try:
        if hasattr(client, "start_generation"):            # SDK v3
            span = client.start_generation(name=name, model=model,
                                           input=prompt, output=output)
        else:                                              # SDK v4+
            span = client.start_observation(name=name, as_type="generation",
                                            model=model, input=prompt,
                                            output=output)
        span.end()
    except Exception as exc:
        # Observability must never break the mission — but it must not vanish
        # in silence either, so the first failure is reported once.
        if not _langfuse_warned:
            _langfuse_warned = True
            print(f"[langfuse] generation logging disabled after error: "
                  f"{exc!r}", flush=True)
