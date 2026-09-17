"""LLM backends for the agent service.

Two interchangeable backends behind one interface, ``complete(prompt) -> str``:

- ``OllamaLLM``  — real local inference via an Ollama server (set OLLAMA_HOST,
  OLLAMA_PORT and OLLAMA_MODEL in the environment).
- ``MockLLM``    — a deterministic stand-in with the *failure surface* of a
  real model: it wraps JSON in chatty prose, drops required fields, emits
  labels outside the requested vocabulary and invents tool names. It lets the
  whole tutorial run with zero setup, and it keeps the integration layer
  honest — every defense in agent_service/main.py is exercised either way.

Both backends track ``calls`` / ``prompt_tokens`` / ``completion_tokens`` the
way an API bill would.

Optional: if LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST are
set (see README), every completion is also logged to Langfuse as a
generation via ``log_generation``.
"""
import hashlib
import json
import os
import random
import re

import requests

SECTORS = ("A1", "A2", "A3", "B1", "B2", "B3")


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


class MockLLM:
    """Deterministic mock: the reply depends only on the prompt text (and how
    often this instance has seen that exact prompt), so every run of the
    tutorial behaves the same. A retry that quotes the failure ("previous
    reply ...") always gets a clean answer — real models merely become more
    likely to comply when shown their error."""

    def __init__(self):
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self._seen = {}

    def complete(self, prompt):
        self.calls += 1
        self.prompt_tokens += len(prompt) // 4
        attempt = self._seen.get(prompt, 0)
        self._seen[prompt] = attempt + 1
        digest = hashlib.sha256(f"{attempt}|{prompt}".encode()).digest()
        rng = random.Random(int.from_bytes(digest[:8], "big"))
        out = self._respond(prompt, rng)
        self.completion_tokens += len(out) // 4
        return out

    def _respond(self, prompt, rng):
        corrected = "previous reply" in prompt
        if "You may call tools" in prompt:
            return self._tools(prompt, rng)
        if "Produce a mission plan" in prompt:
            return self._plan(prompt, rng, corrected)
        if "Classify the field report" in prompt:
            return self._route(prompt, rng, corrected)
        if "Summarize the detections" in prompt:
            return self._summarize(prompt, rng, corrected)
        if "Greet the operator" in prompt:
            return ("SAR mission assistant online — six sectors monitored, "
                    "three drones ready. How can I help?")
        return ("I'm the tutorial's mock LLM. I know these task markers: "
                "'Produce a mission plan', 'Classify the field report', "
                "'Summarize the detections', 'Greet the operator', "
                "'You may call tools'.")

    # -- structured mission plan --
    def _plan(self, prompt, rng, corrected):
        m = re.search(r"Sector: ([A-B][1-3])", prompt)
        sector = m.group(1) if m else rng.choice(SECTORS)
        plan = {"objective": f"sweep sector {sector}",
                "assigned_drone": rng.choice([1, 2, 3]),
                "waypoints": [[round(rng.uniform(0, 40), 1),
                               round(rng.uniform(0, 40), 1)] for _ in range(3)]}
        if not corrected and rng.random() < 0.35:
            kind = rng.random()
            if kind < 0.35:      # chatty prose around perfectly good JSON
                return ("Sure! Here is the mission plan you asked for:\n"
                        + json.dumps(plan) + "\nLet me know if you need changes.")
            if kind < 0.60:      # required field silently dropped
                return json.dumps({k: v for k, v in plan.items()
                                   if k != "waypoints"})
            if kind < 0.80:      # truncated mid-generation: invalid JSON
                return json.dumps(plan)[:-15]
            return ("I recommend sweeping the sector in a serpentine pattern "
                    "at 40 m altitude, prioritizing thermal contrast.")
        return json.dumps(plan)

    # -- triage routing label --
    def _route(self, prompt, rng, corrected):
        report = prompt.split("REPORT:", 1)[-1].lower()
        if any(w in report for w in ("injur", "bleed", "unconscious", "trapped")):
            label = "medical"
        elif any(w in report for w in ("collaps", "gas", "flood")):
            label = "structural"
        elif any(w in report for w in ("suppl", "water", "food", "blanket")):
            label = "logistics"
        else:
            label = "ignore"
        if not corrected:
            r = rng.random()
            if r < 0.32 and "urgent" in report:
                return "urgent"  # a label outside the vocabulary
            if r < 0.35:         # ignores "exactly one word"
                return (f"This sounds like a {label} issue. "
                        f"I'd classify it as: {label}.")
        return label

    # -- per-sector detection summary (reads the detections FROM the prompt,
    #    the way a real model would) --
    def _summarize(self, prompt, rng, corrected):
        m = re.search(r"sector ([A-B][1-3])", prompt)
        sector = m.group(1) if m else "A1"
        try:
            dets = json.loads(prompt.split("DETECTIONS:", 1)[1].split("\n", 1)[0])
        except (IndexError, ValueError):
            dets = []
        persons = [d for d in dets if d.get("kind") == "person"]
        summary = {"sector": sector, "victims": len(persons),
                   "min_confidence": (min(d["confidence"] for d in persons)
                                      if persons else None),
                   "notable": (f"{len(dets)} detection(s), "
                               f"{len(persons)} person(s)") if dets
                              else "no detections"}
        if not corrected:
            r = rng.random()
            if r < 0.12:         # counts spelled out — wrong type
                words = {0: "zero", 1: "one", 2: "two", 3: "three"}
                bad = dict(summary)
                bad["victims"] = words.get(summary["victims"], "several")
                return json.dumps(bad)
            if r < 0.20:
                return "Here's the summary:\n" + json.dumps(summary)
        return json.dumps(summary)

    # -- agentic tool use: decide the next call from the QUESTION, answer
    #    from the OBSERVATION lines already fed back into the prompt --
    def _tools(self, prompt, rng):
        question = prompt.split("QUESTION:", 1)[-1].split("\n", 1)[0]
        ql = question.lower()
        wants_conditions = any(w in ql for w in
                               ("trustworthy", "confidence", "conditions",
                                "weather", "visibility"))
        needed = []
        sectors = re.findall(r"\b([A-B][1-3])\b", question)
        for s in sectors:
            needed.append(("get_detections", {"sector": s}))
            if wants_conditions:
                needed.append(("weather", {"sector": s}))
        for d in re.findall(r"drone (\d)", ql):
            needed.append(("drone_status", {"drone_id": int(d)}))

        for name, args in needed:
            tag = f"OBSERVATION {name}({json.dumps(args, sort_keys=True)})"
            if tag not in prompt:
                # Occasionally invents a near-miss tool name; once the loop
                # feeds back an ERROR line it behaves.
                if "ERROR" not in prompt and rng.random() < 0.25:
                    name = name[:-1] if name.endswith("s") else name + "_check"
                return json.dumps({"tool": name, "args": args})

        observations = self._parse_observations(prompt)
        parts = []
        for s in sectors:
            dets = observations.get(("get_detections", s), {}).get("detections")
            if dets is None:
                continue
            if not dets:
                parts.append(f"sector {s} shows no detections")
                continue
            d = min(dets, key=lambda x: x.get("confidence", 1.0))
            line = f"sector {s}: {d['kind']} at confidence {d['confidence']}"
            conditions = observations.get(("weather", s), {}).get("conditions")
            if conditions:
                line += f", conditions {conditions}"
                if d["confidence"] < 0.7 and conditions != "clear":
                    line += " — treat as unverified until re-checked"
            parts.append(line)
        for d in re.findall(r"drone (\d)", ql):
            st = observations.get(("drone_status", int(d)))
            if st:
                parts.append(f"drone {d} is {st['status']} with battery "
                             f"{st['battery']}%")
        answer = "; ".join(parts) if parts else "I could not determine that."
        return json.dumps({"final": answer})

    @staticmethod
    def _parse_observations(prompt):
        """OBSERVATION lines -> {(tool, key-arg): result-dict}."""
        found = {}
        for m in re.finditer(r"OBSERVATION (\w+)\((\{.*?\})\) -> (.+)", prompt):
            name, args, result = m.group(1), m.group(2), m.group(3)
            try:
                args, result = json.loads(args), json.loads(result)
            except ValueError:
                continue
            key = args.get("sector", args.get("drone_id"))
            found[(name, key)] = result
        return found


def get_llm():
    """OllamaLLM when configured, MockLLM otherwise."""
    host, model = os.getenv("OLLAMA_HOST"), os.getenv("OLLAMA_MODEL")
    if host and model:
        return OllamaLLM(host, os.getenv("OLLAMA_PORT", "11434"), model)
    return MockLLM()


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
