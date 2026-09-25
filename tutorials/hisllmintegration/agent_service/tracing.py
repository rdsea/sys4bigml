"""Send the agent's OpenTelemetry spans to Langfuse as well as Jaeger.

How it works:
  - There is ONE set of spans. Langfuse is attached to the service's
    existing TracerProvider, so Jaeger and Langfuse see the same span tree.
  - Langfuse only exports spans it recognises as LLM-related. Ours are
    custom spans, so the helpers here add `langfuse.*` attributes to them
    (observation type, input/output, model, usage).
  - `_should_export_span` sends only spans that have an observation type.
    Jaeger still gets everything.

Langfuse is optional: without API keys every helper here does nothing.
"""
import json
import os
import re

from opentelemetry import trace

LANGFUSE_ENABLED = False
_client = None

ENVIRONMENT = os.getenv("LANGFUSE_ENVIRONMENT", "development")
RELEASE = os.getenv("LANGFUSE_RELEASE", "his-llm-tutorial")

# Langfuse attribute names, imported from the SDK (not hardcoded) so a
# rename fails loudly.
try:
    from langfuse import LangfuseOtelSpanAttributes as LF
except ImportError:                                        # SDK not installed
    LF = None


# ---------------------------------------------------------------------------
# Masking
# ---------------------------------------------------------------------------

# Patterns redacted before data is sent to Langfuse. There is no personal
# data today; add your own patterns to `_SECRET` as needed.
_SECRET = re.compile(
    r"(sk-[A-Za-z0-9_\-]{8,}"          # API keys
    r"|pk-lf-[A-Za-z0-9_\-]{8,}"       # Langfuse public keys
    r"|Bearer\s+[A-Za-z0-9._\-]{8,}"   # bearer tokens
    r"|[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",  # e-mail
    re.IGNORECASE)


def mask(data):
    """Redact secrets from data created through the Langfuse SDK API.

    Does not cover our own OTel span attributes; `mask_otel_spans` does that.
    """
    try:
        if isinstance(data, str):
            return _SECRET.sub("[REDACTED]", data)
        if isinstance(data, dict):
            return {k: mask(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return [mask(v) for v in data]
        return data
    except Exception:
        return "[MASKING FAILED]"


def mask_otel_spans(*, params):
    """Redact secrets from span attributes before Langfuse exports them.

    This is the hook that covers our prompts and payloads.
    If it raises, Langfuse drops the whole batch (safer than leaking).
    Only affects Langfuse; Jaeger still receives the unmasked spans.
    """
    from langfuse import OtelSpanPatch
    from langfuse.types import MaskOtelSpansResult

    patches = {}
    for identifier, span in params.spans.items():
        changes = {}
        for key, value in (span.attributes or {}).items():
            try:
                if isinstance(value, str):
                    redacted = _SECRET.sub("[REDACTED]", value)
                    if redacted != value:
                        changes[key] = redacted
            except Exception:
                # Replace the value rather than fail the whole batch.
                changes[key] = "[MASKING FAILED]"
        if changes:
            patches[identifier] = OtelSpanPatch(set_attributes=changes)
    return MaskOtelSpansResult(span_patches=patches)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def _should_export_span(span):
    """Export only spans that have a Langfuse observation type set."""
    attributes = getattr(span, "attributes", None) or {}
    return LF.OBSERVATION_TYPE in attributes


def init_langfuse(tracer_provider):
    """Attach Langfuse to the service's tracer provider.

    Returns the client, or None if Langfuse is not configured.
    """
    global LANGFUSE_ENABLED, _client
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        return None
    if LF is None:
        print("[langfuse] SDK not installed; tracing to Langfuse disabled",
              flush=True)
        return None
    try:
        from langfuse import Langfuse
        _client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
            # Reuse the existing provider: one set of spans.
            tracer_provider=tracer_provider,
            should_export_span=_should_export_span,
            mask=mask,
            mask_otel_spans=mask_otel_spans,
            # Lets you filter tutorial runs in the Langfuse UI.
            environment=ENVIRONMENT,
            release=RELEASE,
        )
        LANGFUSE_ENABLED = True
        print(f"[langfuse] tracing enabled -> "
              f"{os.getenv('LANGFUSE_HOST', 'http://localhost:3000')}",
              flush=True)
        return _client
    except Exception as exc:
        # Tracing errors must not stop the service.
        print(f"[langfuse] disabled after init error: {exc!r}", flush=True)
        return None


def flush():
    """Send buffered spans to Langfuse. Called on FastAPI shutdown."""
    if _client is not None:
        try:
            _client.flush()
        except Exception as exc:
            print(f"[langfuse] flush failed: {exc!r}", flush=True)


# ---------------------------------------------------------------------------
# Annotating spans. Each helper writes to the CURRENT OpenTelemetry span.
# ---------------------------------------------------------------------------

def _dump(value, limit=8000):
    """Convert to a JSON string, cut to `limit` characters."""
    try:
        text = value if isinstance(value, str) else json.dumps(value, default=str)
    except Exception:
        text = str(value)
    return text if len(text) <= limit else text[:limit] + "…[truncated]"


def at_start(obs_type, **metadata):
    """Attributes to pass when CREATING a span:
    `tracer.start_as_current_span(name, attributes=at_start("agent"))`.

    The observation type must be set at creation. Langfuse decides the
    trace's root span when a span starts; if the type is added later, no
    span is marked as root. Input, output and usage can be added afterwards.
    """
    if LF is None:
        return {}
    attributes = {LF.OBSERVATION_TYPE: obs_type}
    # Set environment/release on each span: the values passed to Langfuse()
    # only apply to spans the SDK creates, not ours.
    attributes[LF.ENVIRONMENT] = ENVIRONMENT
    attributes[LF.VERSION] = RELEASE
    for key, value in metadata.items():
        attributes[f"{LF.OBSERVATION_METADATA}.{key}"] = (
            value if isinstance(value, (str, int, float, bool)) else _dump(value))
    return attributes


def observe(obs_type, input=None, output=None, metadata=None, level=None,
            status_message=None, span=None):
    """Mark the current span as a Langfuse observation and attach data.

    `obs_type`: span, generation, event, embedding, agent, tool, chain,
    retriever, guardrail or evaluator.
    input/output are only attached when Langfuse is enabled, so Jaeger spans
    stay small.
    """
    span = span or trace.get_current_span()
    if LF is None or not span.is_recording():
        return
    span.set_attribute(LF.OBSERVATION_TYPE, obs_type)
    if level:
        span.set_attribute(LF.OBSERVATION_LEVEL, level)
    if status_message:
        span.set_attribute(LF.OBSERVATION_STATUS_MESSAGE, status_message)
    if metadata:
        for key, value in metadata.items():
            # The prefix makes the key filterable in Langfuse.
            span.set_attribute(f"{LF.OBSERVATION_METADATA}.{key}",
                               value if isinstance(value, (str, int, float, bool))
                               else _dump(value))
    if not LANGFUSE_ENABLED:
        return
    if input is not None:
        span.set_attribute(LF.OBSERVATION_INPUT, _dump(input))
    if output is not None:
        span.set_attribute(LF.OBSERVATION_OUTPUT, _dump(output))


def observe_generation(model, input, output, usage=None, metadata=None,
                       span=None):
    """Mark the current span as an LLM `generation` with model and token usage.

    Langfuse needs both model and usage to calculate cost.
    """
    observe("generation", input=input, output=output, metadata=metadata,
            span=span)
    span = span or trace.get_current_span()
    if LF is None or not span.is_recording():
        return
    if model:
        span.set_attribute(LF.OBSERVATION_MODEL, model)
    if usage:
        span.set_attribute(LF.OBSERVATION_USAGE_DETAILS, json.dumps(
            {k: v for k, v in usage.items() if isinstance(v, int)}))


def trace_attributes(name, session_id=None, tags=None, metadata=None,
                     user_id=None):
    """Context manager that sets trace name, session, tags and metadata on
    every span created inside it (needed for Langfuse filters to work).

    Does nothing when Langfuse is off.
    """
    if not LANGFUSE_ENABLED:
        import contextlib
        return contextlib.nullcontext()
    from langfuse import propagate_attributes
    return propagate_attributes(trace_name=name, session_id=session_id,
                                user_id=user_id, tags=tags,
                                metadata=metadata or {})


def score(name, value, comment=None, data_type=None):
    """Attach a score to the current trace.

    Use for results known only after the work is done (human verdict,
    error count). Tags can't be used because they are set at creation.
    """
    if _client is None:
        return
    try:
        _client.score_current_trace(name=name, value=value, comment=comment,
                                    **({"data_type": data_type} if data_type else {}))
    except Exception as exc:
        print(f"[langfuse] score {name!r} failed: {exc!r}", flush=True)
