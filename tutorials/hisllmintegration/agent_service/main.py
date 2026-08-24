# FastAPI imports
from fastapi import FastAPI, HTTPException
import json
import os
import re

import requests

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Prometheus metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
# Mount /metrics endpoint
from prometheus_client import make_asgi_app

from llm import get_langfuse, get_llm, log_generation

# OTEL environment variables
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "agent_service")
DETECTION_API = os.getenv("DETECTION_SERVICE_API_URL", "http://detection_service:8000")
HUMAN_API = os.getenv("HUMAN_SERVICE_API_URL", "http://human_service:8002/review")

# --------------------------
# OpenTelemetry Tracing Setup
# --------------------------
resource = Resource(attributes={"service.name": SERVICE_NAME})
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)
RequestsInstrumentor().instrument()

# --------------------------
# OpenTelemetry Metrics Setup
# --------------------------
metric_reader = PrometheusMetricReader()
meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(SERVICE_NAME)

request_counter = meter.create_counter(
    "agent_requests_total",
    description="Total requests handled by the agent service")
llm_request_counter = meter.create_counter(
    "agent_llm_requests_total",
    description="Total LLM calls from agent service")
llm_retry_counter = meter.create_counter(
    "agent_llm_retries_total",
    description="LLM calls that failed parse/validation and were retried")
external_service_counter = meter.create_counter(
    "agent_external_requests_total",
    description="Total requests to external services")

# LLM backend (Ollama when configured, deterministic mock otherwise)
llm = get_llm()
langfuse = get_langfuse()
MODEL_NAME = os.getenv("OLLAMA_MODEL", "mock-llm")

# FastAPI app
app = FastAPI(title=SERVICE_NAME)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/metrics", make_asgi_app())
FastAPIInstrumentor.instrument_app(app)


def llm_complete(prompt, task):
    """Every model call is a span carrying the semantic payload — and,
    when configured, a Langfuse generation."""
    llm_request_counter.add(1)
    with tracer.start_as_current_span("llm.complete") as span:
        span.set_attribute("llm.task", task)
        span.set_attribute("llm.is_retry", "previous reply" in prompt)
        out = llm.complete(prompt)
        span.set_attribute("llm.prompt.preview", prompt[:120])
        span.set_attribute("llm.output.preview", out[:120])
        log_generation(langfuse, task, prompt, out, MODEL_NAME)
        return out


# ---------------------------------------------------------------------------
# The integration layer: the model returns TEXT; the mission needs DATA.
# parse liberally -> validate strictly -> retry with the error quoted,
# under a bounded budget. Every defense here fires against the mock AND
# against a real Ollama model.
# ---------------------------------------------------------------------------

FEEDBACK = ("\nYour previous reply was invalid: {error}. "
            "Reply in the requested format only.")


def extract_json(text):
    """First JSON value found in `text`, or None (models wrap JSON in prose)."""
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                obj, _ = decoder.raw_decode(text[i:])
            except ValueError:
                continue
            return obj
    return None


def reliable_call(prompt, parse, validate, task, max_attempts=3):
    """Call the model until parse+validate succeed; the error string is fed
    back verbatim, so validators double as model feedback."""
    p, error = prompt, "no attempt made"
    for attempt in range(max_attempts):
        obj = parse(llm_complete(p, task))
        error = "reply contained no JSON" if obj is None else validate(obj)
        if error is None:
            return obj
        llm_retry_counter.add(1)
        p = prompt + FEEDBACK.format(error=error)
    raise HTTPException(502, f"LLM task {task!r} failed after "
                             f"{max_attempts} attempts: {error}")


# ---------------------------------------------------------------------------
# Tools: the model REQUESTS calls; this dispatcher EXECUTES them against the
# detection_service over HTTP. The model never touches the system directly.
# ---------------------------------------------------------------------------

TOOL_SPECS = [
    {"name": "get_detections", "args": {"sector": "one of A1,A2,A3,B1,B2,B3"},
     "returns": "{sector, detections: [{kind, confidence, pos}]}"},
    {"name": "drone_status", "args": {"drone_id": "1, 2 or 3"},
     "returns": "{drone_id, battery, sector, status}"},
    {"name": "weather", "args": {"sector": "one of A1,A2,A3,B1,B2,B3"},
     "returns": "{sector, conditions}"},
]

TOOL_ROUTES = {
    "get_detections": lambda args: f"{DETECTION_API}/detections/{args['sector']}",
    "drone_status": lambda args: f"{DETECTION_API}/drones/{args['drone_id']}",
    "weather": lambda args: f"{DETECTION_API}/weather/{args['sector']}",
}


def call_tool(name, args):
    if name not in TOOL_ROUTES:
        raise ValueError(f"unknown tool {name!r}; valid tools: "
                         f"{sorted(TOOL_ROUTES)}")
    external_service_counter.add(1)
    with tracer.start_as_current_span(f"tool.{name}") as span:
        span.set_attribute("tool.args", json.dumps(args))
        resp = requests.get(TOOL_ROUTES[name](args), timeout=10)
        if resp.status_code == 404:
            raise ValueError(resp.json().get("detail", "not found"))
        resp.raise_for_status()
        return resp.json()


TOOL_PROMPT = ("You may call tools to gather facts before answering.\n"
               "TOOLS: {specs}\n"
               'Reply with exactly one JSON object per turn: '
               '{{"tool": "<name>", "args": {{...}}}} to call a tool, '
               'or {{"final": "<answer>"}} when you can answer.\n'
               "Each result comes back as an OBSERVATION line. Never request a "
               "tool whose OBSERVATION is already present — repeating a call "
               "returns the same data and wastes the step budget. As soon as "
               "the observations are enough to answer, reply with "
               '{{"final": "<answer>"}}, quoting the numbers you observed.\n'
               "QUESTION: {question}\n")

# The accumulated OBSERVATION/ERROR lines are appended after the question, so
# without this cue the prompt would *end* mid-transcript and a small model
# simply continues the pattern it sees — emitting tool calls forever. The cue
# is re-appended per turn instead of being baked into the history, so it stays
# the last thing the model reads.
TOOL_TURN_CUE = ('Reply with the next single JSON object now '
                 '({"tool": ...} to gather more, {"final": ...} to answer):\n')

# Spent budget must still yield an answer attempt: on the last step the tool
# option is withdrawn entirely, so the only reply left is the answer.
TOOL_FINAL_CUE = ('No tool calls remain. Using ONLY the OBSERVATION lines '
                  'above, reply now with exactly '
                  '{"final": "<answer>"} and nothing else:\n')


def validate_final(obj):
    """The terminal reply has one legal shape; the message doubles as the
    feedback a stuck model gets quoted back at it."""
    if not isinstance(obj, dict) or "final" not in obj:
        return ('reply must be {"final": "<answer>"} — the tool budget is '
                'spent, no tool call can be executed')
    if not isinstance(obj["final"], str) or not obj["final"].strip():
        return '"final" must be a non-empty string'
    return None


def force_final(prompt):
    """Withdrawing the tool option is a *hint*; small models emit tool calls
    anyway. So the terminal answer gets the same parse -> validate -> retry
    discipline as every other structured call in this service, under its own
    bounded budget."""
    return reliable_call(prompt + TOOL_FINAL_CUE, extract_json, validate_final,
                         task="tool_loop")["final"]


def run_tool_loop(question, max_steps=8, max_stalls=2):
    """The agentic inner loop: model decides WHAT it wants, dispatcher
    decides WHETHER it happens; tool errors go back as conversation."""
    prompt = TOOL_PROMPT.format(specs=json.dumps(TOOL_SPECS), question=question)
    steps, observed, stalls = [], set(), 0
    for step in range(max_steps):
        # A model that has stalled (repeating calls it already has) will not
        # un-stall on its own: spend the remaining budget on the answer
        # instead of on identical requests.
        if step == max_steps - 1 or stalls >= max_stalls:
            return force_final(prompt), steps
        reply = extract_json(llm_complete(prompt + TOOL_TURN_CUE, "tool_loop"))
        if isinstance(reply, dict) and "final" in reply:
            return reply["final"], steps
        if isinstance(reply, dict) and "tool" in reply:
            name, args = reply["tool"], reply.get("args", {})
            call = f"{name}({json.dumps(args, sort_keys=True)})"
            # A model that keeps re-requesting data it already has is a real
            # failure mode (small models loop here). The dispatcher refuses
            # rather than paying for the call again — the repeat costs one
            # step of budget and comes back as conversation, not as traffic.
            if call in observed:
                stalls += 1
                steps.append({"repeat": name, "args": args})
                prompt += (f"ERROR: OBSERVATION {call} is already above; "
                           f"requesting it again returns identical data. "
                           f'Answer now with {{"final": "<answer>"}}\n')
                continue
            stalls = 0
            try:
                result = call_tool(name, args)
            except (ValueError, TypeError, requests.RequestException) as exc:
                steps.append({"error": name, "args": args})
                prompt += f"ERROR: {exc}\n"
                continue
            observed.add(call)
            steps.append({"tool": name, "args": args})
            prompt += (f"OBSERVATION {name}({json.dumps(args, sort_keys=True)}) "
                       f"-> {json.dumps(result)}\n")
            continue
        prompt += 'ERROR: reply with {"tool": ...} or {"final": ...} only\n'
    raise HTTPException(502, f"tool loop: no final answer after {max_steps} steps")


# ---------------------------------------------------------------------------
# Workflows: model calls composed along paths designed in code.
# ---------------------------------------------------------------------------

SUMMARY_PROMPT = (
    "Summarize the detections for sector {sector}.\n"
    "DETECTIONS: {detections}\n"
    "Reply with one JSON object and nothing else: no prose, no code fences.\n"
    "Keys:\n"
    '  "sector": the string "{sector}"\n'
    '  "victims": how many detections have kind "person", as an integer '
    "(0 if none) — a count, never a list\n"
    '  "min_confidence": the lowest confidence among those person detections, '
    "a number in (0, 1]; null when victims is 0, a number whenever victims "
    "is greater than 0\n"
    '  "notable": one short sentence describing what stands out\n'
    "An empty DETECTIONS list is normal, not a missing input: summarize it as "
    "an empty sector rather than asking for more information.\n"
    'Example reply for an empty list: {{"sector": "{sector}", "victims": 0, '
    '"min_confidence": null, "notable": "no detections"}}')

# The grounded counterpart: the counts are gone from the prompt entirely,
# because code computes them. What is left is the one job on this page that
# genuinely needs a language model — turning a list of records into a
# sentence a rescue coordinator can read at a glance.
NOTABLE_PROMPT = (
    "Describe sector {sector} for a rescue coordinator in one short sentence.\n"
    "DETECTIONS: {detections}\n"
    "Reply with one JSON object and nothing else: no prose, no code fences.\n"
    'Keys:\n  "notable": one short sentence describing what stands out\n'
    "Do not count anything and do not report confidence numbers — those are "
    "computed elsewhere. Describe only what stands out.\n"
    "An empty DETECTIONS list is normal, not a missing input.\n"
    'Example reply for an empty list: {{"notable": "no detections"}}')

TRIAGE_PROMPT = ("Classify the field report into one of: medical, structural, "
                 "logistics, ignore.\n"
                 "Reply with exactly one lowercase word.\n"
                 "REPORT: {report}")

TRIAGE_LABELS = ("medical", "structural", "logistics", "ignore")


def victim_counts(detections):
    """The arithmetic, in the one place that can be exactly right.

    Called from two directions: `validate_summary` uses it to judge what the
    model claimed, and `summarize_sector_grounded` uses it instead of asking.
    """
    persons = [d for d in detections if d.get("kind") == "person"]
    return (len(persons),
            min(d["confidence"] for d in persons) if persons else None)


def validate_summary(sector, detections):
    """Shape AND substance.

    Type checks only ever proved the reply was well-formed, never that it was
    true: {"victims": 1, "min_confidence": 0.95} is a perfectly valid summary
    of a sector whose only detection is debris. So the two fields the model
    was asked to DERIVE are recomputed here from the same detections the
    prompt carried, and a plausible-looking count is rejected like any other
    malformed reply.

    Worth naming the obvious: whatever the validator can compute, the model
    should not have been asked for. These two fields stay in the prompt
    because watching a real model miss them — miscounting kinds, rounding
    0.84 to 0.85 — is the lesson.
    """
    true_victims, true_min_conf = victim_counts(detections)

    def validate(obj):
        if not isinstance(obj, dict):
            return "summary is not a JSON object"
        if obj.get("sector") != sector:
            return f"sector must be {sector!r}"
        if not isinstance(obj.get("victims"), int) or obj["victims"] < 0:
            return "victims must be a non-negative integer"
        mc = obj.get("min_confidence")
        if mc is not None and not (isinstance(mc, (int, float)) and 0 < mc <= 1):
            return "min_confidence must be null or a number in (0, 1]"
        # -- substance: recomputed from DETECTIONS, never taken on trust --
        if obj["victims"] != true_victims:
            return (f"victims must be {true_victims}: only detections with "
                    f'kind "person" count toward it')
        if true_min_conf is None:
            if mc is not None:
                return "min_confidence must be null when victims is 0"
        elif mc is None or abs(mc - true_min_conf) > 1e-9:
            return (f"min_confidence must be {true_min_conf}: the lowest "
                    f"confidence among the person detections in DETECTIONS, "
                    f"copied exactly and not rounded")
        return None
    return validate


def summarize_sector(sector):
    """One worker: fetch the sector's detections, have the LLM summarize,
    validate the result against those same detections."""
    detections = call_tool("get_detections", {"sector": sector})["detections"]
    prompt = SUMMARY_PROMPT.format(sector=sector,
                                   detections=json.dumps(detections))
    return reliable_call(prompt, extract_json,
                         validate_summary(sector, detections),
                         task=f"summarize_{sector}")


def validate_notable(obj):
    if not isinstance(obj, dict):
        return "reply is not a JSON object"
    if not isinstance(obj.get("notable"), str) or not obj["notable"].strip():
        return '"notable" must be a non-empty string'
    return None


def summarize_sector_grounded(sector):
    """The same worker with the division of labour reversed: code counts, the
    model only writes the sentence.

    `summarize_sector` asks the model to filter a list by a field and take a
    minimum, then spends a retry budget checking whether it did. This one
    never asks. The counts are exact by construction — there is no claim left
    to validate, so no retry can be needed and no mission can fail on
    arithmetic. What the model still does here is the part code is bad at.

    Both workers return the same shape, so everything downstream — the map,
    the human panel, the feedback loop — cannot tell them apart.
    """
    detections = call_tool("get_detections", {"sector": sector})["detections"]
    victims, min_confidence = victim_counts(detections)
    notable = reliable_call(
        NOTABLE_PROMPT.format(sector=sector, detections=json.dumps(detections)),
        extract_json, validate_notable, task=f"describe_{sector}")["notable"]
    return {"sector": sector, "victims": victims,
            "min_confidence": min_confidence, "notable": notable}


def survey_all(grounded=False):
    """Parallelizable fan-out over sectors (kept sequential for reproducible
    traces); the merge is code, not another model call."""
    worker = summarize_sector_grounded if grounded else summarize_sector
    with tracer.start_as_current_span("phase.survey") as span:
        span.set_attribute("survey.summary_mode",
                           "grounded" if grounded else "model")
        external_service_counter.add(1)
        resp = requests.get(f"{DETECTION_API}/sectors", timeout=10)
        resp.raise_for_status()
        sectors = resp.json()["sectors"]
        return {s: worker(s) for s in sectors}


# ---------------------------------------------------------------------------
# The agent: goal fixed (an approved victim map), path decided at runtime.
# Gates ordered by cost: free code check before the scarce human panel.
# ---------------------------------------------------------------------------

def map_valid(victim_map):
    """Gate 1 — 12 lines of Python protect the human panel's attention."""
    if not victim_map:
        return False
    for entry in victim_map:
        if entry.get("sector") is None or not isinstance(entry.get("victims"), int):
            return False
        mc = entry.get("min_confidence")
        if not isinstance(mc, (int, float)) or not 0 < mc <= 1:
            return False
    return True


def build_map(grounded=False):
    survey = survey_all(grounded)
    return [{"sector": s, "victims": v["victims"],
             "min_confidence": v["min_confidence"],
             "notable": v.get("notable")}
            for s, v in sorted(survey.items()) if v["victims"]]


def request_review(victim_map):
    """Gate 2 — Human-as-a-Service. The span is the wait for a human."""
    with tracer.start_as_current_span("human.review") as span:
        external_service_counter.add(1)
        resp = requests.post(HUMAN_API, json={"victim_map": victim_map},
                             timeout=30)
        resp.raise_for_status()
        verdict = resp.json()
        span.set_attribute("decision", verdict["decision"])
        span.set_attribute("reason", verdict["reason"])
        return verdict


def handle_feedback(victim_map, reason):
    """Human feedback is data: parse the named sector, investigate it with
    the tool loop, attach the grounded finding, resubmit."""
    m = re.search(r"sector ([A-B][1-3])", reason)
    if not m:
        return victim_map
    sector = m.group(1)
    answer, _ = run_tool_loop(f"Is the person detection in sector {sector} "
                              f"trustworthy given current conditions there?")
    return [dict(e, note=answer) if e["sector"] == sector else e
            for e in victim_map]


def run_mission(budget=4, grounded=False):
    victim_map, log = None, []
    mode = "grounded" if grounded else "model"
    with tracer.start_as_current_span("sar_mission") as span:
        span.set_attribute("mission.summary_mode", mode)
        for _ in range(budget):
            if victim_map is None or not map_valid(victim_map):
                victim_map = build_map(grounded)
                log.append({"step": "draft",
                            "detail": f"{len(victim_map)} sectors with victims"})
                if not map_valid(victim_map):
                    victim_map = None
                    continue
            verdict = request_review(victim_map)
            log.append({"step": verdict["decision"],
                        "detail": verdict["reason"]})
            if verdict["decision"] == "approve":
                span.set_attribute("mission.outcome", "approved")
                span.set_attribute("mission.model_calls", llm.calls)
                return {"status": "approved", "summary_mode": mode,
                        "victim_map": victim_map,
                        "log": log, "model_calls": llm.calls,
                        "prompt_tokens": llm.prompt_tokens}
            victim_map = handle_feedback(victim_map, verdict["reason"])
        span.set_attribute("mission.outcome", "budget_exhausted")
    raise HTTPException(502, f"mission budget of {budget} iterations exhausted")


# --------------------------
# Endpoints
# --------------------------

@app.get("/greet")
def greet():
    request_counter.add(1)
    return {"message": llm_complete("Greet the operator of the SAR mission "
                                    "system in one sentence.", "greet")}


@app.post("/triage")
def triage(data: dict):
    """Routing workflow: one cheap classify call picks the path."""
    request_counter.add(1)
    report = data.get("report", "")
    with tracer.start_as_current_span("triage") as span:
        label = reliable_call(
            TRIAGE_PROMPT.format(report=report),
            parse=lambda t: t.strip().lower(),
            validate=lambda l: (None if l in TRIAGE_LABELS
                                else f"{l!r} is not one of {TRIAGE_LABELS}"),
            task="triage")
        span.set_attribute("triage.label", label)
        return {"report": report, "label": label}


SUMMARY_MODES = ("model", "grounded")


@app.post("/mission")
def mission(data: dict = None):
    """The full agent loop: draft -> validate -> human review -> react.

    Body: {"summary_mode": "model"} (default) or {"summary_mode": "grounded"}.

    The two modes run the identical loop and differ in one decision — who
    computes the victim counts:

      model     the LLM derives them; `validate_summary` recomputes and
                rejects what disagrees. Honest about what a small model does
                to "filter by field, then take a minimum": llama3.2 reports
                A2's minimum confidence as 0.85 when the data says 0.84, and
                the mission fails outright rather than tasking rescuers off a
                number nobody checked.

      grounded  code derives them and the model only writes the prose. Exact
                by construction, and it cannot fail on arithmetic.

    Run both and diff the result: same endpoint, same panel, same map shape —
    and only one of them can put a victim in a sector that holds debris.
    """
    request_counter.add(1)
    mode = (data or {}).get("summary_mode", "model")
    if mode not in SUMMARY_MODES:
        raise HTTPException(400, f"summary_mode must be one of {SUMMARY_MODES}")
    return run_mission(grounded=(mode == "grounded"))
