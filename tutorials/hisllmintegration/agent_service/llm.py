"""LLM backend for the agent service.

``OllamaLLM.complete(prompt) -> (text, usage)`` calls a local Ollama server
(configured by OLLAMA_HOST, OLLAMA_PORT, OLLAMA_MODEL).

It also counts ``calls``, ``prompt_tokens`` and ``completion_tokens``.
Tracing is done in ``tracing.py``.
"""
import os
import threading

import requests


class OllamaLLM:
    """Local inference through Ollama's /api/generate endpoint."""

    def __init__(self, host, port, model):
        self.base = f"http://{host}:{port}"
        self.model = model
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        # The parallel pattern calls complete() from several threads, and
        # `+=` is not atomic, so the counters need a lock.
        self._lock = threading.Lock()

    def complete(self, prompt):
        """Return ``(text, usage)``.

        ``usage`` holds the real token counts reported by Ollama. If Ollama
        doesn't report them, they are estimated as characters / 4 and
        ``usage["estimated"]`` is True.
        """
        resp = requests.post(f"{self.base}/api/generate",
                             json={"model": self.model, "prompt": prompt,
                                   "stream": False},
                             timeout=120)
        resp.raise_for_status()
        body = resp.json()
        out = body.get("response", "")

        prompt_tokens = body.get("prompt_eval_count")
        completion_tokens = body.get("eval_count")
        estimated = prompt_tokens is None or completion_tokens is None
        if estimated:
            prompt_tokens = len(prompt) // 4
            completion_tokens = len(out) // 4

        with self._lock:
            self.calls += 1
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens

        usage = {"input": prompt_tokens, "output": completion_tokens,
                 "total": prompt_tokens + completion_tokens,
                 "estimated": estimated}
        return out, usage


def get_llm():
    """Create the OllamaLLM from env vars. Raises if host or model is missing."""
    host = os.getenv("OLLAMA_HOST") or ""
    model = os.getenv("OLLAMA_MODEL") or ""
    if not (host and model):
        raise RuntimeError(
            "OLLAMA_HOST and OLLAMA_MODEL must be set — install Ollama "
            "(https://ollama.com), pull a model (e.g. `ollama pull llama3.2`) "
            "and set them in .env (see .env.example).")
    return OllamaLLM(host, os.getenv("OLLAMA_PORT") or "11434", model)
