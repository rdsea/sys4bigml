"""The SAR agent: five LLM patterns, each one switchable per request.

Each pattern has two code paths:
  - ON:  the disciplined version the pattern prescribes.
  - OFF: the naive version most people write first.
`Patterns` (patterns.py) holds the flags that pick the path.

The OFF paths do not crash. They finish, record what went wrong in
`run.issues`, and `score_map` compares the result with ground truth.
"""
# FastAPI imports
from fastapi import FastAPI, HTTPException
import concurrent.futures as futures
import json
import os
import re
import threading
import time
import uuid

import requests

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry import context as otel_context
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.utils import _SUPPRESS_INSTRUMENTATION_KEY

# Prometheus metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
# Mount /metrics endpoint
from prometheus_client import make_asgi_app

import tracing
from llm import get_llm
from patterns import KEYS, PATTERNS, Patterns, used_by

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
# Counts wrong values that reached the output because a pattern was off.
unchecked_error_counter = meter.create_counter(
    "agent_unchecked_errors_total",
    description="Model claims that reached the output contradicting ground "
                "truth, because the pattern that would have caught them was off")

# LLM backend (local Ollama inference)
llm = get_llm()
MODEL_NAME = os.getenv("OLLAMA_MODEL")

# Langfuse reuses the tracer provider above (see tracing.py).
# Returns None if Langfuse is not configured.
langfuse = tracing.init_langfuse(tracer_provider)

# FastAPI app
app = FastAPI(title=SERVICE_NAME)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/metrics", make_asgi_app())
FastAPIInstrumentor.instrument_app(app)


# ---------------------------------------------------------------------------
# Run: state for one request (flags, steps, issues, cost).
# The LLM counters are process-wide, so Run stores their start values and
# reports the difference for this request only.
# ---------------------------------------------------------------------------

class Run:
    """Collects steps, issues and cost for one request.

    Uses a lock because the parallel pattern writes from several threads.
    """

    def __init__(self, flags, task, session_id=None, request=None):
        self.flags = flags
        self.task = task
        # Langfuse session id. /compare passes the same id to both runs so
        # they appear together in the session view.
        self.session_id = session_id or f"{task}-{uuid.uuid4().hex[:12]}"
        self.request = request or {}
        self.steps = []
        self.issues = []
        self.retries = 0
        self.tool_calls = 0
        self._lock = threading.Lock()
        self._t0 = time.time()
        self._calls0 = llm.calls
        self._tokens0 = llm.prompt_tokens

    def step(self, step, actor, detail):
        """Record one step of the task for the console timeline.

        `actor` is who did it: "AI" (the LLM agent), "S" (plain software)
        or "H" (the human panel). Same labels as tools/mission_analytics.py.
        """
        with self._lock:
            self.steps.append({"step": step, "actor": actor, "detail": detail})

    def issue(self, pattern, detail):
        """Record a problem that the (disabled) `pattern` would have caught."""
        with self._lock:
            self.issues.append({"pattern": pattern, "detail": detail})

    def bump(self, retries=0, tool_calls=0):
        with self._lock:
            self.retries += retries
            self.tool_calls += tool_calls

    def metrics(self, extra=None):
        return {"model_calls": llm.calls - self._calls0,
                "prompt_tokens": llm.prompt_tokens - self._tokens0,
                "retries": self.retries,
                "tool_calls": self.tool_calls,
                "elapsed_ms": round((time.time() - self._t0) * 1000),
                **(extra or {})}


def tag_patterns(span, flags):
    """Write the pattern flags onto `span`.

    `run.patterns` (e.g. "all", "structured+routing") is what the analytics
    tool groups by; `patterns.<key>` lets you filter single flags in Jaeger.
    """
    span.set_attribute("run.patterns", flags.label())
    span.set_attribute("run.patterns_on", flags.enabled_count())
    for key in KEYS:
        span.set_attribute(f"patterns.{key}", getattr(flags, key))


def llm_complete(prompt, task):
    """Call the LLM once, inside a traced span.

    Jaeger gets short previews of the prompt and output. Langfuse gets the
    full text, model name and token usage as a `generation`.
    One call = one generation, so each step of an agent loop stays visible.
    """
    llm_request_counter.add(1)
    is_retry = "previous reply" in prompt
    with tracer.start_as_current_span(
            "llm.complete", attributes=tracing.at_start("generation")) as span:
        span.set_attribute("llm.task", task)
        span.set_attribute("llm.is_retry", is_retry)
        out, usage = llm.complete(prompt)
        span.set_attribute("llm.prompt.preview", prompt[:120])
        span.set_attribute("llm.output.preview", out[:120])
        span.set_attribute("llm.tokens.input", usage["input"])
        span.set_attribute("llm.tokens.output", usage["output"])
        tracing.observe_generation(
            model=MODEL_NAME, input=prompt, output=out, usage=usage,
            metadata={"task": task, "is_retry": is_retry,
                      "usage_estimated": usage["estimated"]})
        return out


# ===========================================================================
# PATTERN 1 — Structured outputs: parse -> validate -> retry
#
# Why: the model returns text, but the mission needs exact data (victim
# counts, confidences). Wrong numbers must not reach the map.
#   ON:  parse leniently, validate against the source data, retry with the
#        error message.
#   OFF: json.loads once and trust the result.
# ===========================================================================

FEEDBACK = ("\nYour previous reply was invalid: {error}. "
            "Reply in the requested format only.")


def extract_json(text):
    """Return the first JSON value found in `text`, or None.

    Lenient: models often wrap JSON in extra prose.
    """
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                obj, _ = decoder.raw_decode(text[i:])
            except ValueError:
                continue
            return obj
    return None


def reliable_call(prompt, parse, validate, task, run=None, max_attempts=3):
    """PATTERN ON. Retry until parse and validate succeed.

    The validator's error message is added to the next prompt.
    Raises HTTP 502 after `max_attempts`.
    """
    p, error = prompt, "no attempt made"
    for attempt in range(max_attempts):
        obj = parse(llm_complete(p, task))
        error = "reply contained no JSON" if obj is None else validate(obj)
        if error is None:
            return obj
        llm_retry_counter.add(1)
        if run:
            run.bump(retries=1)
        p = prompt + FEEDBACK.format(error=error)
    raise HTTPException(502, f"LLM task {task!r} failed after "
                             f"{max_attempts} attempts: {error}")


def naive_call(prompt, task, run, fallback=None):
    """PATTERN OFF. One call, strict json.loads, no validation, no retry.

    A parse failure is recorded as an issue and `fallback` is returned.
    A reply that parses but is wrong is accepted silently.
    """
    raw = llm_complete(prompt, task)
    try:
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        run.issue("structured",
                  f"{task}: reply did not parse as JSON ({exc}); "
                  f"no retry was attempted. Raw reply began: {raw[:80]!r}")
        return fallback


def structured_call(prompt, validate, task, run, fallback=None):
    """Switch for pattern 1: `reliable_call` if ON, `naive_call` if OFF.

    The OFF path never raises, so the task finishes even if the data is wrong.
    """
    if run.flags.structured:
        return reliable_call(prompt, extract_json, validate, task, run=run)
    return naive_call(prompt, task, run, fallback=fallback)


# ===========================================================================
# PATTERN 2 — Tool use through a controlled dispatcher
#
# Why: the model knows nothing about this disaster area. Facts must come
# from detection_service, not from the model's memory.
#   ON:  the model asks for a tool by name; the dispatcher checks the
#        allowlist and makes the HTTP call itself.
#   OFF: no tools; the model answers from memory.
# ===========================================================================

TOOL_SPECS = [
    {"name": "get_detections", "args": {"sector": "one of A1,A2,A3,B1,B2,B3"},
     "returns": "{sector, detections: [{kind, confidence, pos}]}"},
    {"name": "drone_status", "args": {"drone_id": "1, 2 or 3"},
     "returns": "{drone_id, battery, sector, status}"},
    {"name": "weather", "args": {"sector": "one of A1,A2,A3,B1,B2,B3"},
     "returns": "{sector, conditions}"},
]

# Tool allowlist: tool name -> URL builder. Only names listed here can be
# called, and the model never supplies a URL.
TOOL_ROUTES = {
    "get_detections": lambda args: f"{DETECTION_API}/detections/{args['sector']}",
    "drone_status": lambda args: f"{DETECTION_API}/drones/{args['drone_id']}",
    "weather": lambda args: f"{DETECTION_API}/weather/{args['sector']}",
}


def call_tool(name, args, run=None):
    """Run an allowlisted tool over HTTP. Raises ValueError for an unknown
    tool or a 404, so the error can be shown to the model."""
    if name not in TOOL_ROUTES:
        raise ValueError(f"unknown tool {name!r}; valid tools: "
                         f"{sorted(TOOL_ROUTES)}")
    external_service_counter.add(1)
    if run:
        run.bump(tool_calls=1)
    with tracer.start_as_current_span(
            f"tool.{name}", attributes=tracing.at_start("tool", tool=name)) as span:
        span.set_attribute("tool.args", json.dumps(args))
        resp = requests.get(TOOL_ROUTES[name](args), timeout=10)
        if resp.status_code == 404:
            detail = resp.json().get("detail", "not found")
            tracing.observe("tool", input=args, output={"error": detail},
                            level="ERROR", status_message=detail,
                            metadata={"tool": name})
            raise ValueError(detail)
        resp.raise_for_status()
        result = resp.json()
        # Type `tool` so Langfuse shows it as a tool call in the agent graph.
        tracing.observe("tool", input=args, output=result,
                        metadata={"tool": name})
        return result


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

# Added at the end of every turn's prompt. Without it, small models keep
# copying the OBSERVATION lines and call tools forever.
TOOL_TURN_CUE = ('Reply with the next single JSON object now '
                 '({"tool": ...} to gather more, {"final": ...} to answer):\n')

# Used on the last step: tools are no longer allowed, only a final answer.
TOOL_FINAL_CUE = ('No tool calls remain. Using ONLY the OBSERVATION lines '
                  'above, reply now with exactly '
                  '{"final": "<answer>"} and nothing else:\n')

# PATTERN OFF: no tools exist, so the question goes straight to the weights.
UNAIDED_PROMPT = ("Answer the question about the search-and-rescue area.\n"
                  "QUESTION: {question}\n"
                  "Reply with one JSON object and nothing else: "
                  '{{"final": "<answer>"}}')


# Default question for /investigate and /compare. Sector B1 has one person
# detection at 0.62 confidence, in smoke. Kept to a single fact because
# small models handle multi-part questions poorly in the tool loop.
DEFAULT_QUESTION = ("Is the person detection in sector B1 trustworthy given "
                    "current conditions there?")


def validate_final(obj):
    """Check the reply is {"final": "<non-empty string>"}."""
    if not isinstance(obj, dict) or "final" not in obj:
        return ('reply must be {"final": "<answer>"} — the tool budget is '
                'spent, no tool call can be executed')
    if not isinstance(obj["final"], str) or not obj["final"].strip():
        return '"final" must be a non-empty string'
    return None


def force_final(prompt, run):
    """Ask for the final answer only (no more tools).

    Goes through `structured_call`, because small models may still try to
    call a tool here.
    """
    obj = structured_call(prompt + TOOL_FINAL_CUE, validate_final,
                          task="tool_loop", run=run,
                          fallback={"final": "(no answer produced)"})
    return (obj or {}).get("final", "(no answer produced)")


def run_tool_loop(question, run, max_steps=8, max_stalls=2):
    """PATTERN ON. The tool loop.

    Each turn the model replies with a tool call or a final answer. Tool
    results are added as OBSERVATION lines, errors as ERROR lines.
    Returns (answer, steps).
    """
    prompt = TOOL_PROMPT.format(specs=json.dumps(TOOL_SPECS), question=question)
    steps, observed, stalls = [], set(), 0
    for step in range(max_steps):
        # Last step, or the model keeps repeating calls: force an answer.
        if step == max_steps - 1 or stalls >= max_stalls:
            return force_final(prompt, run), steps
        reply = extract_json(llm_complete(prompt + TOOL_TURN_CUE, "tool_loop"))
        if isinstance(reply, dict) and "final" in reply:
            return reply["final"], steps
        if isinstance(reply, dict) and "tool" in reply:
            name, args = reply["tool"], reply.get("args", {})
            call = f"{name}({json.dumps(args, sort_keys=True)})"
            # Repeated call: don't re-run it, tell the model to answer instead.
            if call in observed:
                stalls += 1
                steps.append({"repeat": name, "args": args})
                prompt += (f"ERROR: OBSERVATION {call} is already above; "
                           f"requesting it again returns identical data. "
                           f'Answer now with {{"final": "<answer>"}}\n')
                continue
            stalls = 0
            try:
                result = call_tool(name, args, run=run)
            except (ValueError, TypeError, requests.RequestException) as exc:
                # Unknown tool or failed call: show the error to the model.
                steps.append({"error": name, "args": args, "detail": str(exc)})
                prompt += f"ERROR: {exc}\n"
                continue
            observed.add(call)
            steps.append({"tool": name, "args": args})
            prompt += (f"OBSERVATION {name}({json.dumps(args, sort_keys=True)}) "
                       f"-> {json.dumps(result)}\n")
            continue
        prompt += 'ERROR: reply with {"tool": ...} or {"final": ...} only\n'
    raise HTTPException(502, f"tool loop: no final answer after {max_steps} steps")


def answer_unaided(question, run):
    """PATTERN OFF. No tools: the model answers from memory, so the answer
    is not based on real data."""
    obj = structured_call(UNAIDED_PROMPT.format(question=question),
                          validate_final, task="unaided", run=run,
                          fallback={"final": "(no answer produced)"})
    run.issue("dispatcher",
              "answered from model memory with no tool call: nothing in this "
              "reply was read from detection_service")
    return (obj or {}).get("final", "(no answer produced)"), []


def investigate(question, run):
    """Switch for pattern 2: tool loop if ON, unaided answer if OFF."""
    with tracer.start_as_current_span(
            "investigate", attributes=tracing.at_start("agent")) as span:
        span.set_attribute("question", question[:120])
        tag_patterns(span, run.flags)
        # Type `agent`: this step decides the flow and calls tools.
        tracing.observe("agent", input={"question": question},
                        metadata={"dispatcher": run.flags.dispatcher})
        if run.flags.dispatcher:
            answer, steps = run_tool_loop(question, run)
        else:
            answer, steps = answer_unaided(question, run)
        span.set_attribute("tool.calls", run.tool_calls)
        tracing.observe("agent", output={"answer": answer, "steps": steps})
        return answer, steps


# ===========================================================================
# PATTERN 3 — Workflow: routing
#
# Why: reports are mixed (medical, structural, logistics, noise). Pick the
# path before doing the expensive work.
#   ON:  one cheap classify call, then a specialist prompt. "ignore" stops
#        there.
#   OFF: one generalist prompt handles every report.
# Used by /triage (one report) and /mission (a batch, see `triage_reports`).
# ===========================================================================

TRIAGE_PROMPT = ("Classify the field report into one of: medical, structural, "
                 "logistics, ignore.\n"
                 "Reply with exactly one lowercase word.\n"
                 "REPORT: {report}")

TRIAGE_LABELS = ("medical", "structural", "logistics", "ignore")

# Specialist prompts, one per label.
HANDLER_PROMPTS = {
    "medical": ("You are the medical dispatcher for a disaster response.\n"
                "REPORT: {report}\n"
                "Reply with one JSON object and nothing else.\n"
                'Keys: "action": one sentence naming the medical response to '
                'task now; "priority": one of "immediate", "urgent", '
                '"routine".'),
    "structural": ("You are the structural engineering lead for a disaster "
                   "response.\n"
                   "REPORT: {report}\n"
                   "Reply with one JSON object and nothing else.\n"
                   'Keys: "action": one sentence naming the structural '
                   'assessment or shoring to task now; "priority": one of '
                   '"immediate", "urgent", "routine".'),
    "logistics": ("You are the logistics coordinator for a disaster "
                  "response.\n"
                  "REPORT: {report}\n"
                  "Reply with one JSON object and nothing else.\n"
                  'Keys: "action": one sentence naming the supply or '
                  'transport move to task now; "priority": one of '
                  '"immediate", "urgent", "routine".'),
}

# PATTERN OFF: one general prompt for every report.
GENERALIST_PROMPT = (
    "You handle every incoming field report for a disaster response: medical, "
    "structural, logistics, and reports not worth acting on.\n"
    "REPORT: {report}\n"
    "Reply with one JSON object and nothing else.\n"
    'Keys: "label": one of medical, structural, logistics, ignore; '
    '"action": one sentence naming what to task now; '
    '"priority": one of "immediate", "urgent", "routine".')


def validate_handler(obj):
    """Check a specialist reply: non-empty "action" and a valid "priority"."""
    if not isinstance(obj, dict):
        return "reply is not a JSON object"
    if not isinstance(obj.get("action"), str) or not obj["action"].strip():
        return '"action" must be a non-empty string'
    if obj.get("priority") not in ("immediate", "urgent", "routine"):
        return '"priority" must be one of "immediate", "urgent", "routine"'
    return None


def validate_generalist(obj):
    """Same as `validate_handler`, plus a valid "label"."""
    error = validate_handler(obj)
    if error:
        return error
    if obj.get("label") not in TRIAGE_LABELS:
        return f'"label" must be one of {TRIAGE_LABELS}'
    return None


def handle_report(report, run):
    """Switch for pattern 3.

    ON:  classify into one label, then call that label's specialist.
         "ignore" returns without a second call.
    OFF: one generalist call classifies and responds together.
    """
    with tracer.start_as_current_span(
            "triage", attributes=tracing.at_start("chain")) as span:
        tag_patterns(span, run.flags)
        tracing.observe("chain", input={"report": report},
                        metadata={"routing": run.flags.routing})
        if not run.flags.routing:
            span.set_attribute("triage.route", "generalist")
            run.step("handle", "AI", "handled by one general prompt (no routing)")
            obj = structured_call(GENERALIST_PROMPT.format(report=report),
                                  validate_generalist, task="generalist",
                                  run=run, fallback={}) or {}
            label = obj.get("label", "unknown")
            span.set_attribute("triage.label", str(label))
            run.issue("routing",
                      "one general prompt handled this report; a junk report "
                      "still costs a full-length answer")
            return {"label": label, "action": obj.get("action"),
                    "priority": obj.get("priority"), "route": "generalist"}

        # -- routing on: classify, then dispatch --
        # The classifier replies with one word, not JSON, so it can't use
        # `structured_call`. It uses its own parse function instead.
        prompt = TRIAGE_PROMPT.format(report=report)
        classify = lambda l: (None if l in TRIAGE_LABELS
                              else f"{l!r} is not one of {TRIAGE_LABELS}")
        if run.flags.structured:
            label = reliable_call(prompt,
                                  parse=lambda t: t.strip().lower().strip(".\"'"),
                                  validate=classify, task="triage", run=run)
        else:
            # Naive: use the raw reply. Replies like "medical." or "The report
            # is medical" won't match any label and can't be routed.
            label = llm_complete(prompt, "triage").strip().lower()
            if label not in TRIAGE_LABELS:
                run.issue("structured",
                          f"classifier returned {label[:60]!r}, which is not "
                          f"one of {TRIAGE_LABELS}; without validation, the "
                          f"report is not sent to any specialist")
        span.set_attribute("triage.label", label)
        run.step("classify", "AI", f"report classified as {label!r}")

        if label == "ignore":
            span.set_attribute("triage.route", "dropped")
            run.step("drop", "S", "dropped; no specialist call needed")
            return {"label": label, "action": None, "priority": None,
                    "route": "dropped"}
        if label not in HANDLER_PROMPTS:
            span.set_attribute("triage.route", "unroutable")
            return {"label": label, "action": None, "priority": None,
                    "route": "unroutable"}

        span.set_attribute("triage.route", label)
        run.step("dispatch", "S", f"handed to the {label} specialist")
        obj = structured_call(HANDLER_PROMPTS[label].format(report=report),
                              validate_handler, task=f"handler_{label}",
                              run=run, fallback={}) or {}
        return {"label": label, "action": obj.get("action"),
                "priority": obj.get("priority"), "route": label}


# Field reports the mission triages when the request doesn't supply any:
# one for each route, including a junk report that routing should drop.
DEFAULT_REPORTS = (
    "Two people trapped under a collapsed wall on Oak Street, one is "
    "bleeding badly.",
    "A crack is spreading across the east wall of the school gym and the "
    "roof is sagging.",
    "Water and blankets are running low at the B3 staging area; the access "
    "road is blocked.",
    "Radio check, testing one two three.",
)


def reports_from(data):
    """Field reports from the request body, or DEFAULT_REPORTS."""
    reports = data.get("reports")
    if reports is None:
        return DEFAULT_REPORTS
    if not isinstance(reports, list) or not all(isinstance(r, str)
                                                for r in reports):
        raise HTTPException(400, "reports must be a list of strings")
    return tuple(reports)


def triage_reports(reports, run):
    """Mission phase: run each field report through `handle_report`.

    If one report fails (validator gave up), it is recorded with route
    "failed" and the mission carries on.
    """
    with tracer.start_as_current_span(
            "phase.field_reports", attributes=tracing.at_start("chain")) as span:
        span.set_attribute("reports.count", len(reports))
        tracing.observe("chain", input={"reports": list(reports)},
                        metadata={"routing": run.flags.routing})
        results = []
        for report in reports:
            try:
                results.append({"report": report,
                                **handle_report(report, run)})
            except HTTPException as exc:
                run.step("report_failed", "S",
                         f"report could not be handled: {exc.detail}")
                results.append({"report": report, "label": None,
                                "action": None, "priority": None,
                                "route": "failed"})
        tracing.observe("chain", output=results)
        return results


# ===========================================================================
# PATTERN 4 — Workflow: parallelization
#
# Why: the six sector summaries are independent, so run them at the same time.
#   ON:  run them concurrently in a thread pool.
#   OFF: run them one after another.
# Same calls and same results; only the total time changes.
# ===========================================================================

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

# Grounded mode: code computes the counts; the model only writes the
# one-sentence description.
NOTABLE_PROMPT = (
    "Describe sector {sector} for a rescue coordinator in one short sentence.\n"
    "DETECTIONS: {detections}\n"
    "Reply with one JSON object and nothing else: no prose, no code fences.\n"
    'Keys:\n  "notable": one short sentence describing what stands out\n'
    "Do not count anything and do not report confidence numbers — those are "
    "computed elsewhere. Describe only what stands out.\n"
    "An empty DETECTIONS list is normal, not a missing input.\n"
    'Example reply for an empty list: {{"notable": "no detections"}}')

# Dispatcher OFF: no detections are fetched, so the model is asked to
# report them from memory.
RECALL_PROMPT = (
    "Report the current drone detections for sector {sector} of the "
    "search-and-rescue area.\n"
    "Reply with one JSON object and nothing else: no prose, no code fences.\n"
    "Keys:\n"
    '  "sector": the string "{sector}"\n'
    '  "victims": how many people are detected there, as an integer\n'
    '  "min_confidence": the lowest detection confidence, a number in (0, 1], '
    "or null when victims is 0\n"
    '  "notable": one short sentence describing what stands out')


def victim_counts(detections):
    """Return (number of "person" detections, their lowest confidence).

    Used by `validate_summary`, grounded mode in `summarize_sector`, and
    `score_map`.
    """
    persons = [d for d in detections if d.get("kind") == "person"]
    return (len(persons),
            min(d["confidence"] for d in persons) if persons else None)


def validate_summary(sector, detections):
    """Build a validator for one sector's summary.

    Checks the shape (types) and the values: `victims` and `min_confidence`
    are recomputed from `detections` and must match exactly.
    (Grounded mode avoids asking the model for these at all.)
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
        # -- values: must match what we compute from the detections --
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


def validate_notable(obj):
    """Check the reply has a non-empty "notable" string."""
    if not isinstance(obj, dict):
        return "reply is not a JSON object"
    if not isinstance(obj.get("notable"), str) or not obj["notable"].strip():
        return '"notable" must be a non-empty string'
    return None


def summarize_sector(sector, run, grounded=False):
    """Summarize one sector. Three possible paths:

    - dispatcher OFF: the model describes the sector from memory.
    - grounded:       fetch detections, code counts, model writes a sentence.
    - default:        fetch detections, model counts, validator checks it.
    """
    if not run.flags.dispatcher:
        # No tools, so there is no real data. Validation can only check the
        # shape, because there are no detections to compare the counts with.
        run.issue("dispatcher",
                  f"sector {sector} was described from model memory: no tool "
                  f"call was made, so nothing here was read from "
                  f"detection_service")
        if run.flags.structured:
            run.issue("dispatcher",
                      "validation could only check the format: with no tool "
                      "call there are no detections to check the model's "
                      "counts against")
        obj = structured_call(RECALL_PROMPT.format(sector=sector),
                              lambda o: (None if isinstance(o, dict)
                                         else "summary is not a JSON object"),
                              task=f"recall_{sector}", run=run,
                              fallback={}) or {}
        return {"sector": sector,
                "victims": obj.get("victims") if isinstance(obj.get("victims"), int) else 0,
                "min_confidence": obj.get("min_confidence"),
                "notable": obj.get("notable") or "(no description)",
                "source": "model memory"}

    detections = call_tool("get_detections", {"sector": sector},
                           run=run)["detections"]
    if grounded:
        # Code counts; the model only writes the sentence.
        victims, min_confidence = victim_counts(detections)
        obj = structured_call(
            NOTABLE_PROMPT.format(sector=sector,
                                  detections=json.dumps(detections)),
            validate_notable, task=f"describe_{sector}", run=run,
            fallback={}) or {}
        return {"sector": sector, "victims": victims,
                "min_confidence": min_confidence,
                "notable": obj.get("notable") or "(no description)",
                "source": "code-derived"}

    obj = structured_call(
        SUMMARY_PROMPT.format(sector=sector, detections=json.dumps(detections)),
        validate_summary(sector, detections),
        task=f"summarize_{sector}", run=run, fallback={}) or {}
    return {"sector": sector,
            "victims": obj.get("victims") if isinstance(obj.get("victims"), int) else 0,
            "min_confidence": obj.get("min_confidence"),
            "notable": obj.get("notable") or "(no description)",
            "source": "model-derived"}


def survey_all(run, grounded=False):
    """Switch for pattern 4: summarize all sectors in parallel or in order.

    Worker threads start with an empty OpenTelemetry context, so each worker
    attaches the parent context. Otherwise its spans would become separate
    traces instead of children of phase.survey.
    """
    with tracer.start_as_current_span(
            "phase.survey", attributes=tracing.at_start("chain")) as span:
        span.set_attribute("survey.summary_mode",
                           "grounded" if grounded else "model")
        span.set_attribute("survey.parallel", run.flags.parallel)
        # Type `chain`: it runs fixed steps and merges results (no decisions).
        tracing.observe("chain", metadata={"parallel": run.flags.parallel,
                                           "mode": "grounded" if grounded
                                                   else "model"})
        external_service_counter.add(1)
        resp = requests.get(f"{DETECTION_API}/sectors", timeout=10)
        resp.raise_for_status()
        sectors = resp.json()["sectors"]
        span.set_attribute("survey.sectors", len(sectors))

        if not run.flags.parallel:
            run.step("survey", "AI",
                     f"{len(sectors)} sectors summarized one after another")
            return {s: summarize_sector(s, run, grounded) for s in sectors}

        ctx = otel_context.get_current()

        def worker(sector):
            token = otel_context.attach(ctx)
            try:
                return sector, summarize_sector(sector, run, grounded)
            finally:
                otel_context.detach(token)

        run.step("survey", "AI",
                 f"{len(sectors)} sectors summarized concurrently")
        with futures.ThreadPoolExecutor(max_workers=len(sectors)) as pool:
            return dict(pool.map(worker, sectors))


# ===========================================================================
# PATTERN 5 — Agent loop with a human gate
#
# Why: the victim map sends real rescue teams, so a human must approve it,
# and the agent must act on the human's feedback.
#   ON:  draft -> code check -> human review -> investigate rejected sector
#        -> resubmit (up to a budget).
#   OFF: the first draft ships with no review.
# The cheap code check runs before the human panel.
# ===========================================================================

def map_valid(victim_map):
    """Gate 1: cheap code check that every entry has valid fields."""
    if not victim_map:
        return False
    for entry in victim_map:
        if entry.get("sector") is None or not isinstance(entry.get("victims"), int):
            return False
        mc = entry.get("min_confidence")
        if not isinstance(mc, (int, float)) or not 0 < mc <= 1:
            return False
    return True


def build_map(run, grounded=False):
    """Survey all sectors and keep the ones with victims."""
    survey = survey_all(run, grounded)
    return [{"sector": s, "victims": v["victims"],
             "min_confidence": v["min_confidence"],
             "notable": v.get("notable"), "source": v.get("source")}
            for s, v in sorted(survey.items()) if v["victims"]]


def request_review(victim_map, run):
    """Gate 2: send the map to the human panel. Span duration = human wait."""
    with tracer.start_as_current_span(
            "human.review", attributes=tracing.at_start("evaluator")) as span:
        external_service_counter.add(1)
        resp = requests.post(HUMAN_API, json={"victim_map": victim_map},
                             timeout=30)
        resp.raise_for_status()
        verdict = resp.json()
        span.set_attribute("decision", verdict["decision"])
        span.set_attribute("reason", verdict["reason"])
        # Type `evaluator`: the panel judges the agent's output.
        tracing.observe("evaluator", input={"victim_map": victim_map},
                        output=verdict,
                        metadata={"decision": verdict["decision"],
                                  "experts": len(verdict.get("votes", []))})
        # Record the verdict as a Langfuse score.
        tracing.score("human-verdict", verdict["decision"],
                      data_type="CATEGORICAL", comment=verdict["reason"])
        return verdict


def handle_feedback(victim_map, reason, run):
    """Find the sector named in the rejection reason, investigate it with
    the tool loop, and attach the answer as a note on that entry."""
    m = re.search(r"sector ([A-B][1-3])", reason)
    if not m:
        return victim_map
    sector = m.group(1)
    run.step("investigate", "AI",
             f"panel named sector {sector}; checked it with tools and "
             f"added a note")
    answer, _ = investigate(f"Is the person detection in sector {sector} "
                            f"trustworthy given current conditions there?", run)
    return [dict(e, note=answer) if e["sector"] == sector else e
            for e in victim_map]


# ---------------------------------------------------------------------------
# Scoring (tutorial only, not a pattern).
# Compares the final map with the real detections to measure what turning
# a pattern off cost. Production systems have no such ground truth.
# ---------------------------------------------------------------------------

def ground_truth():
    """Read the real victim counts per sector: {sector: (victims, min_conf)}.

    Tracing is suppressed here so these reads don't show up as agent
    traffic (S2S:ai_to_service) in the analytics.
    """
    token = otel_context.attach(
        otel_context.set_value(_SUPPRESS_INSTRUMENTATION_KEY, True))
    try:
        resp = requests.get(f"{DETECTION_API}/sectors", timeout=10)
        resp.raise_for_status()
        truth = {}
        for sector in resp.json()["sectors"]:
            r = requests.get(f"{DETECTION_API}/detections/{sector}", timeout=10)
            r.raise_for_status()
            truth[sector] = victim_counts(r.json()["detections"])
        return truth
    finally:
        otel_context.detach(token)


def score_map(victim_map, run):
    """Count the errors in `victim_map` compared with ground truth.

    If the mission aborted (map is None), nothing is scored: "shipped
    nothing" is reported by `status`, not counted as errors.
    """
    with tracer.start_as_current_span(
            "score", attributes=tracing.at_start("evaluator",
                                                 scorer="ground-truth")) as span:
        tracing.observe("evaluator", input={"victim_map": victim_map},
                        metadata={"scorer": "ground-truth"})
        if victim_map is None:
            span.set_attribute("score.shipped", False)
            return {"scored": False, "errors_shipped": None,
                    "detail": ["nothing was shipped — the run aborted before "
                               "producing a map"]}
        try:
            truth = ground_truth()
        except requests.RequestException as exc:
            return {"scored": False, "errors_shipped": None,
                    "detail": [str(exc)]}
        errors, claimed = [], set()
        for entry in victim_map:
            sector = entry.get("sector")
            claimed.add(sector)
            if sector not in truth:
                errors.append(f"sector {sector!r} does not exist")
                continue
            true_v, true_c = truth[sector]
            if entry.get("victims") != true_v:
                errors.append(f"{sector}: map says {entry.get('victims')} "
                              f"victims, truth is {true_v}")
            mc = entry.get("min_confidence")
            if true_c is not None and (not isinstance(mc, (int, float))
                                       or abs(mc - true_c) > 1e-9):
                errors.append(f"{sector}: map says min_confidence {mc}, "
                              f"truth is {true_c}")
        for sector, (true_v, _) in truth.items():
            if true_v and sector not in claimed:
                errors.append(f"{sector}: {true_v} victims missing from the map")
        if errors:
            unchecked_error_counter.add(len(errors))
        span.set_attribute("score.shipped", True)
        span.set_attribute("score.errors", len(errors))
        span.set_attribute("run.patterns", run.flags.label())
        result = {"scored": True, "errors_shipped": len(errors),
                  "detail": errors}
        tracing.observe("evaluator", output=result,
                        level="WARNING" if errors else "DEFAULT")
        return result


def run_mission(run, budget=4, grounded=False, reports=DEFAULT_REPORTS):
    """Run the full mission: triage field reports, then draft, check and
    review the victim map.

    Returns a result dict instead of raising. Status is one of:
    "approved", "unreviewed", "aborted" (validator gave up) or
    "budget_exhausted". `field_reports` holds the triage result per report.
    """
    mode = "grounded" if grounded else "model"
    with tracer.start_as_current_span(
            "sar_mission",
            attributes=tracing.at_start("agent", summary_mode=mode)) as span:
        span.set_attribute("mission.summary_mode", mode)
        tag_patterns(span, run.flags)
        field_reports = triage_reports(reports, run)
        result = draft_and_review(run, span, budget, grounded)
        result["field_reports"] = field_reports
        return result


def draft_and_review(run, span, budget, grounded):
    """Build the victim map. Switch for pattern 5 (human gate)."""
    victim_map, mode = None, "grounded" if grounded else "model"

    # -- PATTERN OFF: draft once, ship it. --
    if not run.flags.human_gate:
        try:
            victim_map = build_map(run, grounded)
        except HTTPException as exc:
            span.set_attribute("mission.outcome", "aborted")
            return {"status": "aborted", "reason": exc.detail,
                    "victim_map": None}
        run.step("draft", "AI",
                 f"{len(victim_map)} sectors with victims")
        ok = map_valid(victim_map)
        run.step("code_check", "S",
                 "passed the code check (all fields valid)" if ok
                 else "FAILED the code check, but was used anyway")
        run.issue("human_gate",
                  "no human reviewed this map; it was sent straight to "
                  "rescuers")
        span.set_attribute("mission.outcome", "unreviewed")
        return {"status": "unreviewed", "summary_mode": mode,
                "victim_map": victim_map}

    # -- PATTERN ON: draft -> code gate -> panel -> react -> resubmit. --
    for _ in range(budget):
        if victim_map is None or not map_valid(victim_map):
            try:
                victim_map = build_map(run, grounded)
            except HTTPException as exc:
                span.set_attribute("mission.outcome", "aborted")
                return {"status": "aborted", "reason": exc.detail,
                        "victim_map": None}
            run.step("draft", "AI",
                     f"{len(victim_map)} sectors with victims")
            if not map_valid(victim_map):
                run.step("code_check", "S",
                         "failed the code check; redrafting before asking "
                         "the panel")
                victim_map = None
                continue
            run.step("code_check", "S", "passed the code check (all fields valid)")
        verdict = request_review(victim_map, run)
        run.step(verdict["decision"], "H", verdict["reason"])
        if verdict["decision"] == "approve":
            span.set_attribute("mission.outcome", "approved")
            return {"status": "approved", "summary_mode": mode,
                    "victim_map": victim_map}
        victim_map = handle_feedback(victim_map, verdict["reason"], run)
    span.set_attribute("mission.outcome", "budget_exhausted")
    return {"status": "budget_exhausted", "summary_mode": mode,
            "victim_map": victim_map,
            "reason": f"mission budget of {budget} iterations exhausted"}


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def envelope(run, result, score=None):
    """Standard response for every task, so two runs can be compared."""
    return {"patterns": run.flags.as_dict(),
            "pattern_label": run.flags.label(),
            "patterns_on": run.flags.enabled_count(),
            # Flags for other patterns are accepted but have no effect.
            "patterns_used": list(used_by(run.task)),
            "task": run.task,
            **result,
            "steps": run.steps,
            "issues": run.issues,
            "metrics": run.metrics(
                {"errors_shipped": (score or {}).get("errors_shipped")}
                if score else None),
            "score": score}


def flags_from(data, key="patterns"):
    """Build `Patterns` from the request body. Unknown keys -> HTTP 400."""
    try:
        return Patterns((data or {}).get(key))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


def attempt(run, produce, score=None):
    """Run a task under one root span and always return an envelope.

    If the validator gives up (HTTPException), the result has
    status "aborted" instead of returning an HTTP error.
    """
    # One run = one root span = one trace (task and scoring together).
    # Trace attributes are set outside the span so Langfuse applies them to
    # every observation in the trace.
    with tracing.trace_attributes(
            name=f"sar-{run.task}",
            session_id=run.session_id,
            # Tag with the pattern config so runs can be filtered in Langfuse.
            tags=[f"task:{run.task}", f"patterns:{run.flags.label()}",
                  f"patterns-on:{run.flags.enabled_count()}"],
            metadata={f"pattern_{k}": getattr(run.flags, k) for k in KEYS}):
        with tracer.start_as_current_span(
                f"run.{run.task}",
                attributes=tracing.at_start("agent", task=run.task)) as span:
            tag_patterns(span, run.flags)
            # The root's input/output become the trace's input/output.
            tracing.observe("agent", input=run.request,
                            metadata={"task": run.task,
                                      "patterns": run.flags.label(),
                                      "patterns_on": run.flags.enabled_count()})
            try:
                result = produce()
            except HTTPException as exc:
                span.set_attribute("run.status", "aborted")
                tracing.observe("agent", output={"status": "aborted",
                                                 "reason": exc.detail},
                                level="WARNING", status_message=exc.detail)
                # Record the abort as an outcome score.
                tracing.score("outcome", "aborted", data_type="CATEGORICAL",
                              comment=exc.detail)
                return envelope(run, {"status": "aborted",
                                      "reason": exc.detail})
            status = str(result.get("status", "ok"))
            span.set_attribute("run.status", status)
            scored = score(result) if score else None
            tracing.observe("agent", output=result,
                            metadata={"status": status})
            tracing.score("outcome", status, data_type="CATEGORICAL")
            if scored and scored.get("errors_shipped") is not None:
                # Known only after the run, so it is a score, not a tag.
                tracing.score("errors-shipped", float(scored["errors_shipped"]),
                              data_type="NUMERIC",
                              comment="; ".join(scored.get("detail") or [])[:900])
            return envelope(run, result, scored)


# --------------------------
# Endpoints
# --------------------------

@app.on_event("shutdown")
def _flush_langfuse():
    """Send any buffered Langfuse spans before the container stops."""
    tracing.flush()


@app.get("/patterns")
def list_patterns():
    """Return the pattern registry; the console builds its checkboxes from it."""
    return {"patterns": PATTERNS, "keys": list(KEYS)}


@app.get("/greet")
def greet():
    request_counter.add(1)
    return {"message": llm_complete("Greet the operator of the SAR mission "
                                    "system in one sentence.", "greet")}


@app.post("/triage")
def triage(data: dict = None):
    """Handle one field report (pattern 3).
    Body: {"report": "...", "patterns": {...}}"""
    request_counter.add(1)
    data = data or {}
    report = data.get("report", "")
    run = Run(flags_from(data), task="triage", request={"report": report})
    return attempt(run, lambda: handle_report(report, run))


@app.post("/investigate")
def investigate_endpoint(data: dict = None):
    """Answer one question with the tool loop (pattern 2).
    Body: {"question": "...", "patterns": {...}}"""
    request_counter.add(1)
    data = data or {}
    question = data.get("question") or DEFAULT_QUESTION
    run = Run(flags_from(data), task="investigate",
              request={"question": question})

    def produce():
        answer, steps = investigate(question, run)
        return {"question": question, "answer": answer, "tool_steps": steps}

    return attempt(run, produce)


SUMMARY_MODES = ("model", "grounded")


@app.post("/mission")
def mission(data: dict = None):
    """Run the full mission (all five patterns). Body:

        {"summary_mode": "model" | "grounded",
         "reports": ["field report", ...],
         "patterns": {"structured": true, "dispatcher": true, ...}}

    reports: optional; defaults to DEFAULT_REPORTS.
    summary_mode (separate from the patterns):
      "model"    - the model counts victims; the validator checks it.
      "grounded" - code counts victims; the model only describes.
    """
    request_counter.add(1)
    data = data or {}
    mode = data.get("summary_mode", "model")
    if mode not in SUMMARY_MODES:
        raise HTTPException(400, f"summary_mode must be one of {SUMMARY_MODES}")
    reports = reports_from(data)
    run = Run(flags_from(data), task="mission",
              request={"summary_mode": mode, "reports": len(reports)})
    return attempt(run, lambda: run_mission(run, grounded=(mode == "grounded"),
                                            reports=reports),
                   score=lambda r: score_map(r.get("victim_map"), run))


def task_mission(data, run):
    return run_mission(run, grounded=(data.get("summary_mode") == "grounded"),
                       reports=reports_from(data))


def task_triage(data, run):
    return handle_report(data.get("report", ""), run)


def task_investigate(data, run):
    answer, steps = investigate(data.get("question") or DEFAULT_QUESTION, run)
    return {"question": data.get("question") or DEFAULT_QUESTION,
            "answer": answer, "tool_steps": steps}


# Tasks /compare can run. Each returns a plain result dict; `attempt` adds
# the envelope and scoring.
TASKS = {"mission": task_mission,
         "triage": task_triage,
         "investigate": task_investigate}


@app.post("/compare")
def compare(data: dict = None):
    """Run one task twice, with one pattern OFF then ON, and return both.

    Body: {"task": "mission", "pattern": "human_gate", "patterns": {...}}

    `patterns` is the shared baseline; only `pattern` changes between runs.
    `pattern` must be one the task uses (see `used_by`), otherwise HTTP 400.
    """
    request_counter.add(1)
    data = data or {}
    task = data.get("task", "mission")
    if task not in TASKS:
        raise HTTPException(400, f"task must be one of {sorted(TASKS)}")
    key = data.get("pattern")
    if key not in KEYS:
        raise HTTPException(400, f"pattern must be one of {list(KEYS)}")
    # Comparing a pattern the task never uses would show two identical runs.
    if key not in used_by(task):
        raise HTTPException(400, f"task {task!r} does not use pattern {key!r}; "
                                 f"it uses {list(used_by(task))}")
    if task == "mission":
        reports_from(data)  # reject bad `reports` before running anything
    base = flags_from(data)

    arms = {}
    # Same Langfuse session for both runs, so they show up together.
    session_id = f"compare-{key}-{uuid.uuid4().hex[:12]}"
    for state in (False, True):
        run = Run(base.replace(**{key: state}), task=task,
                  session_id=session_id,
                  request={**{k: v for k, v in data.items()
                              if k in ("report", "reports", "question",
                                       "summary_mode")},
                           "compared_pattern": key,
                           "pattern_state": "on" if state else "off"})
        # Give each run its own trace. Both runs are in one HTTP request, so
        # without an empty context they'd share a trace and the analytics
        # could not tell their `run.patterns` apart.
        token = otel_context.attach(otel_context.Context())
        try:
            # Each run is scored separately; an aborted run is still returned.
            arms["on" if state else "off"] = attempt(
                run,
                lambda r=run: TASKS[task](data, r),
                score=(lambda result, r=run: score_map(result.get("victim_map"), r))
                if task == "mission" else None)
        finally:
            otel_context.detach(token)
    return {"task": task, "pattern": key,
            "spec": next(p for p in PATTERNS if p["key"] == key),
            "off": arms["off"], "on": arms["on"]}
