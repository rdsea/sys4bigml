# FastAPI imports
from fastapi import FastAPI
import os
import random
import time

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Prometheus metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
# Mount /metrics endpoint
from prometheus_client import make_asgi_app

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "human_service")

# Configure OTEL Tracing (gRPC)
resource = Resource(attributes={"service.name": SERVICE_NAME})
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# Configure OTEL Metrics (Prometheus)
metric_reader = PrometheusMetricReader()
meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

review_counter = meter.create_counter(
    name="human_review_requests_total",
    description="Total number of human review requests",
    unit="1",
)
rejection_counter = meter.create_counter(
    name="human_review_rejections_total",
    description="Total number of rejected victim maps",
    unit="1",
)

# FastAPI app
app = FastAPI(title=SERVICE_NAME)
app.mount("/metrics", make_asgi_app())
FastAPIInstrumentor.instrument_app(app)

# ---------------------------------------------------------------------------
# Human-as-a-Service: a panel of crowd experts reviews the agent's victim map
# before it reaches rescuers. Each expert applies one review policy; the
# decision is the majority vote. The span DURATION of each vote is the
# simulated human decision latency — the human is a component, and often the
# bottleneck, so the trace should say so.
#
# Rejection reasons follow a fixed vocabulary ("sector <name> ...") so the
# agent can PARSE them and react — human feedback is data, if you design it
# to be.
# ---------------------------------------------------------------------------

CONFIDENCE_FLOOR = 0.7


def vote_confidence(victim_map):
    """expert1: refuses low-confidence sightings without a verification note."""
    for entry in victim_map:
        conf = entry.get("min_confidence")
        if (entry.get("victims") and conf is not None
                and conf < CONFIDENCE_FLOOR and not entry.get("note")):
            return ("reject", f"sector {entry['sector']} sighting is low "
                              f"confidence ({conf}); verify conditions there "
                              f"before I sign off")
    return ("approve", "confidence levels acceptable")


def vote_completeness(victim_map):
    """expert2: refuses empty or structurally hollow maps."""
    if not victim_map:
        return ("reject", "the map is empty — survey the area first")
    if any("sector" not in e or "victims" not in e for e in victim_map):
        return ("reject", "map entries are missing sector or victim counts")
    return ("approve", "map is complete")


def vote_operational(victim_map):
    """expert3: signs off unless the map is unusable for tasking."""
    if not victim_map:
        return ("reject", "nothing to task rescue teams with")
    return ("approve", "usable for rescue tasking")


EXPERTS = {"expert1": vote_confidence,
           "expert2": vote_completeness,
           "expert3": vote_operational}


@app.post("/review")
def review_victim_map(data: dict):
    review_counter.add(1)
    victim_map = data.get("victim_map", [])

    with tracer.start_as_current_span("review_victim_map") as root_span:
        root_span.set_attribute("map_size", len(victim_map))

        votes = []
        for name, policy in EXPERTS.items():
            with tracer.start_as_current_span(f"vote_by_{name}") as vote_span:
                vote_span.set_attribute("expert", name)
                # Simulated thinking time: the span duration IS the
                # human decision latency.
                time.sleep(random.uniform(0.2, 0.6))
                vote, comment = policy(victim_map)
                vote_span.set_attribute("vote", vote)
                votes.append({"expert": name, "vote": vote, "comment": comment})

        # Safety-critical decision: consensus required — any expert can block.
        approvals = sum(v["vote"] == "approve" for v in votes)
        decision = "approve" if approvals == len(votes) else "reject"
        # The reason handed back is the FIRST reject comment: specific,
        # parseable, actionable.
        reason = next((v["comment"] for v in votes if v["vote"] == "reject"),
                      "map accepted for rescue tasking")
        if decision == "reject":
            rejection_counter.add(1)

        root_span.set_attribute("decision", decision)
        root_span.set_attribute("reason", reason)
        return {"decision": decision, "reason": reason, "votes": votes}
